//
// Created by Moritz Herzog on 03.01.25.
//

#include "UploadProjectFileToBackend.h"
#include "Dialogs/CreateProjectDialog.h"
#include "ui_UploadProjectFileToBackend.h"

#include <QMessageBox>
#include <QToolBar>
#include <iostream>

#include <Services/IMqttClientService.h>
#include <boost/property_tree/json_parser.hpp>
#include <boost/property_tree/ptree.hpp>
#include <boost/uuid/random_generator.hpp>
#include <boost/uuid/uuid_io.hpp>
#include <kerml/root/annotations/TextualRepresentation.h>
#include <kerml/root/elements/Element.h>
#include <memory>
#include <sstream>
#include <sysmlv2/rest/entities/Branch.h>
#include <sysmlv2/rest/entities/Commit.h>
#include <sysmlv2/rest/entities/CommitRequest.h>
#include <sysmlv2/rest/entities/DataIdentity.h>
#include <sysmlv2/rest/entities/DataVersion.h>

#include "entities/TwinRequest.h"
// #include "AGILABackendImplementation/DigitalTwin.h"

namespace DigitalTwin::Client {
UploadProjectFileToBackend::UploadProjectFileToBackend(
    BACKEND_COMMUNICATION::CommunicationService *service,
    PHYSICAL_TWIN_COMMUNICATION::IMqttClientService *mqttService,
    const std::string &username, QWidget *parent)
    : QMainWindow(parent), Ui(new Ui::UploadProjectFileToBackend()),
      Parser(new MarkdownParser()), DTElementsModels(new QStandardItemModel()),
      CommunicationService(service), MqttService(mqttService),
      Username(username) {
  Ui->setupUi(this);
  Ui->retranslateUi(this);

  QStringList headerElements;
  headerElements << tr("Code");

  DTElementsModels->setHorizontalHeaderLabels(headerElements);
  Ui->DTModelListView->setModel(DTElementsModels);
  auto toolbar = new QToolBar(this);
  addToolBar(toolbar);

  Ui->actionDownload->setIcon(QIcon(":/icons/Download"));
  toolbar->addAction(Ui->actionDownload);
  Ui->actionUpload->setIcon(QIcon(":/icons/Upload"));
  toolbar->addAction(Ui->actionUpload);

  makeConnections();
}

UploadProjectFileToBackend::~UploadProjectFileToBackend() { delete Ui; }

void UploadProjectFileToBackend::setHTMLTextForView(QString htmlText) {
  Status = UploadProjectFileToBackendStatus::DocumentOpened;
  Parser->parseMarkdownFile(htmlText);
  Elements = Parser->getElementsOfProject();
  this->setWindowModified(false);
  redecorateWithStatusChange();
}

void UploadProjectFileToBackend::onTextEdited() {
  this->setWindowModified(true);
}

void UploadProjectFileToBackend::makeConnections() {
  connect(Ui->CreateDTButton, SIGNAL(clicked(bool)), this,
          SLOT(onCreateDigitalTwinClicked()));
  connect(Ui->actionUpload, SIGNAL(triggered(bool)), this,
          SLOT(createOnlineProject()));
}

void UploadProjectFileToBackend::setMarkdownOfOnlineProject(QString Markdown) {
  if (!Markdown.isEmpty()) {
    Parser->parseMarkdown(Markdown);
    Elements = Parser->getElementsOfProject();
  }
  this->setWindowModified(false);
}

void UploadProjectFileToBackend::setElementsForView(
    std::vector<std::shared_ptr<KerML::Entities::Element>> elements,
    std::shared_ptr<SysMLv2::REST::Commit> commit,
    std::shared_ptr<SysMLv2::REST::Project> project) {
  Status = UploadProjectFileToBackendStatus::OnlineProjectOpened;
  Elements = elements;
  Commit = commit;
  Project = project;
  redecorateWithStatusChange();
}

void UploadProjectFileToBackend::setCodeElements() {
  DTElementsModels->clear();
  QStringList headerElements;
  headerElements << tr("Code");
  DTElementsModels->setHorizontalHeaderLabels(headerElements);

  for (const auto &elem : Elements) {
    const auto &textualRep =
        std::dynamic_pointer_cast<KerML::Entities::TextualRepresentation>(elem);
    if (textualRep && !textualRep->body().empty() &&
        (textualRep->language() != "Markdown") &&
        (textualRep->language() != "YaML") &&
        (textualRep->getType() == "TextualRepresentation"))
      DTElementsModels->appendRow(
          new QStandardItem(QString::fromStdString(textualRep->body())));
  }
}

void UploadProjectFileToBackend::createOnlineProject() {
  CreateProjectDialog dialog(this);
  dialog.exec();
  if (dialog.result() == QDialog::DialogCode::Accepted) {
    try {
      Project = CommunicationService->postProject(
          dialog.getProjectName(), dialog.getProjectDecription(), "Main");
    } catch (const std::exception &e) {
      std::cerr << "[Client] postProject failed: " << e.what() << "\n";
      QMessageBox::critical(
          this, tr("Project Creation Failed"),
          QString("Failed to create project on server: %1").arg(e.what()));
      return;
    } catch (...) {
      QMessageBox::critical(this, tr("Project Creation Failed"),
                            tr("Failed to create project on server due to an "
                               "unknown network error."));
      return;
    }

    if (Project) {
      try {
        auto branches = CommunicationService->getAllBranchesForProjectWithID(
            Project->getId());
        for (const auto &branch : branches) {
          if (branch->getHead()) {
            Commit = branch->getHead();
            break;
          }
        }
      } catch (const std::exception &e) {
        std::cerr << "[Client] Failed to fetch branch head commit: " << e.what()
                  << "\n";
      }
    }

    // Dynamic project ACL registration on Broker
    if (MqttService && Project) {
      try {
        boost::property_tree::ptree pt;
        pt.put("username", Username);
        pt.put("projectId", boost::uuids::to_string(Project->getId()));

        std::ostringstream ss;
        boost::property_tree::write_json(ss, pt);

        MqttService->publish("dt/system/register_project", ss.str());
        std::cout << "[Client] Published dynamic project registration to "
                     "broker for project "
                  << boost::uuids::to_string(Project->getId()) << "\n";
      } catch (const std::exception &e) {
        std::cerr
            << "[Client] Failed to publish project registration to broker: "
            << e.what() << "\n";
      }
    }

    std::vector<std::shared_ptr<SysMLv2::REST::DataVersion>> dataVersions;

    if (Commit) {
      Commit->setChange(dataVersions);
    }

    Status = UploadProjectFileToBackendStatus::OnlineProjectOpened;
    redecorateWithStatusChange();
    this->setWindowModified(false);
  }
}

void UploadProjectFileToBackend::redecorateWithStatusChange() {
  if (Status == UploadProjectFileToBackendStatus::OnlineProjectOpened ||
      Status == UploadProjectFileToBackendStatus::DocumentOpened) {
    setCodeElements();
    QString markdown;
    for ([[maybe_unused]] const auto &elem : Elements) {
      // markdown += QString::fromStdString(elem->getMarkdownString());
    }
    setMarkdownOfOnlineProject(markdown);
    Ui->actionDownload->setDisabled(false);
    Ui->actionUpload->setDisabled(false);
    Ui->DTTab->setDisabled(false);
  } else {
    Ui->actionUpload->setDisabled(false);
    Ui->actionDownload->setDisabled(true);
    Ui->DTTab->setDisabled(true);
  }
}

void UploadProjectFileToBackend::onCreateDigitalTwinClicked() {
  if (!Project) {
    QMessageBox::warning(this, tr("No Online Project"),
                         tr("Please click the Upload button (in top toolbar) "
                            "first to upload and create the project on the "
                            "server before creating a Digital Twin."));
    return;
  }

  if (!Commit) {
    try {
      auto branches = CommunicationService->getAllBranchesForProjectWithID(
          Project->getId());
      for (const auto &branch : branches) {
        if (branch->getHead()) {
          Commit = branch->getHead();
          break;
        }
      }
    } catch (const std::exception &e) {
      std::cerr << "[Client] Exception getting branches: " << e.what() << "\n";
    }
  }

  if (!Commit) {
    QMessageBox::warning(this, tr("No Commit Found"),
                         tr("Cannot create Digital Twin: No commit found on "
                            "the server for this project."));
    return;
  }

  std::vector<std::shared_ptr<KerML::Entities::Element>> elements;
  for (const auto &elem : Elements) {
    const auto &textRep =
        std::dynamic_pointer_cast<KerML::Entities::TextualRepresentation>(elem);
    if (textRep && !textRep->body().empty() &&
        (textRep->language() != "Markdown") &&
        (textRep->language() != "YaML") &&
        (textRep->getType() == "TextualRepresentation"))
      elements.push_back(textRep);
  }

  std::vector<boost::uuids::uuid> selectedElements;

  const auto selectedItems =
      Ui->DTModelListView->selectionModel()->selectedRows();
  for (const auto &element : selectedItems) {
    if (element.row() >= 0 &&
        static_cast<size_t>(element.row()) < elements.size()) {
      selectedElements.push_back(elements[element.row()]->getId());
    }
  }

  std::shared_ptr<SysMLv2::REST::TwinRequest> twinRequest =
      std::make_shared<SysMLv2::REST::TwinRequest>(
          Ui->DTNameLineEdit->text().toStdString(), Commit);

  try {
    CommunicationService->postDigitalTwin(twinRequest, Project->getId());
    QMessageBox::information(this, tr("Success"),
                             tr("Digital Twin created successfully!"));
  } catch (const std::exception &e) {
    QMessageBox::critical(
        this, tr("Error"),
        QString("Failed to create Digital Twin: %1").arg(e.what()));
  }
}

} // namespace DigitalTwin::Client
