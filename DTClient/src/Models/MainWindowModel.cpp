//
// Created by Moritz Herzog on 14.05.24.
//

#include <QList>
#include <BECommunicationService.h>
#include <string>
#include <sysmlv2/rest/entities/Project.h>
//#include "AGILABackendImplementation/DigitalTwin.h"
#include <DigitalTwinManager.h>
#include <Services/MqttClientService.h>
#include <sysmlv2/rest/entities/Branch.h>
#include <sysmlv2/rest/entities/Commit.h>
#include <kerml/root/elements/Element.h>

#include <QFile>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QSet>
#include <QDir>
#include <boost/uuid/uuid_io.hpp>
#include <boost/lexical_cast.hpp>

#include "MainWindowModel.h"
#include "DigitalTwinClientSettings.h"
#include "../Widgets/DigitalTwinMainWindow.h"
#include "../Widgets/TreeViewModels/ProjectTreeViewModel.h"
#include "../Widgets/DigitalTwinTabWidget/DigitalTwinTabWidget.h"
#include "../Widgets/UploadProjectFileToBackend.h"
#include "Markdown/MarkdownParser.h"

#include "MqttConnectionThread.h"
#include "entities/DigitalTwin.h"


namespace DigitalTwin::Client {
    MainWindowModel::MainWindowModel(DigitalTwinMainWindow *mainWindow) {
        MainWindow = mainWindow;
        Settings = new DigitalTwinClientSettings(MainWindow);
        Status = MainWindowStatus::NOT_CONNECTED;
        decorateTreeView();
    }

    MainWindowModel::~MainWindowModel() {
        delete Settings;
        delete ProjectViewModel;
        delete DigitalTwinManager;
        if(BackendCommunication != nullptr)
            delete BackendCommunication;
        if(DigitalTwinManager != nullptr)
            delete DigitalTwinManager;
        if(ConnectionThread != nullptr)
            delete ConnectionThread;
    }

    void MainWindowModel::connectToBackend() {
        try {
            BackendCommunication=new BACKEND_COMMUNICATION::CommunicationService(Settings->getRESTServerAsString(),std::stoi(Settings->getRESTPortAsString()), Settings->getRESTFolderAsString());
            ConnectionThread = new MQTTConnectionThread(Settings->getMQTTServerAsString(), Settings->getMQTTPortAsString(),
                                                        Settings->getRESTUserAsString(), Settings->getRESTPasswordAsString());
            ConnectionThread->start();
            DigitalTwinManager = new DigitalTwin::DigitalTwinManager(BackendCommunication, ConnectionThread->getClientService());
            BackendCommunication->setUserForLoginInBackend(Settings->getRESTUserAsString(),Settings->getRESTPasswordAsString());
            Status = MainWindowStatus::CONNECTED;

            refreshProjects();

        }catch (std::exception &ex){
            qDebug()<<ex.what();
        }
    }

    DigitalTwinClientSettings *MainWindowModel::clientSettings() const {
        return Settings;
    }

    void MainWindowModel::openMarkdownFile(QString filePath) {
        UploadProjectFileToBackend *uploadFileDialog = new UploadProjectFileToBackend(BackendCommunication, MainWindow);
        uploadFileDialog->setHTMLTextForView(filePath);
        uploadFileDialog->show();
    }

    bool MainWindowModel::isOnline()
    {
        return (BackendCommunication != nullptr);
    }

    void MainWindowModel::decorateTreeView() {
        ProjectViewModel = new ViewModels::ProjectTreeViewModel(MainWindow);
        MainWindow->setProjectTreeViewModel(ProjectViewModel);
    }

    void MainWindowModel::onTreeViewClicked(const QModelIndex &index) {
        auto item = ProjectViewModel->getProjectTreeViewItemFromIndex(index);

        auto possibleDigitalTwin = item->getDigitalTwin();
        if(possibleDigitalTwin != nullptr){
            auto model = DigitalTwinManager->addDigitalTwinAndCreateModel(possibleDigitalTwin);
            MainWindow->addTabWidget(new DigitalTwinTabWidget(model,MainWindow),QString::fromStdString(possibleDigitalTwin->getName()));
        } else if(item->getProject() != nullptr) {
            auto project = item->getProject();
            UploadProjectFileToBackend* uploadFileDialog = new UploadProjectFileToBackend(BackendCommunication, MainWindow);
            auto branches = BackendCommunication->getAllBranchesForProjectWithID(project->getId());
            std::vector<std::shared_ptr<KerML::Entities::Element>> elements;
            std::shared_ptr<SysMLv2::REST::Commit> commit = nullptr;
            for (const auto& branch : branches) {
                if (branch->getId() == project->getDefaultBranch()->getId()) {
                    commit = branch->getHead();
                    elements = BackendCommunication->getAllElements(branch->getHead()->getId(), project->getId());
                }
            }

            uploadFileDialog->setElementsForView(elements,commit,project);
            uploadFileDialog->show();
        }
    }

    void MainWindowModel::connectToDigitalTwin() {

    }

    void MainWindowModel::refreshProjects() {
        auto rawProjects = BackendCommunication->getAllProjects();
        Projects.clear();

        QString username = QString::fromStdString(Settings->getRESTUserAsString());
        QString aclFileName = "users_acl.json";
        QString aclFilePath = "";

        // Traverse up parent directories to find users_acl.json (relative lookup)
        QDir dir = QDir::current();
        for (int i = 0; i < 5; ++i) {
            if (dir.exists(aclFileName)) {
                aclFilePath = dir.absoluteFilePath(aclFileName);
                break;
            }
            if (!dir.cdUp()) {
                break;
            }
        }

        if (aclFilePath.isEmpty()) {
            qDebug() << "[GUI] users_acl.json not found in hierarchy, allowing all projects.";
            Projects = rawProjects;
        } else {
            qDebug() << "[GUI] Loading Access Control List from:" << aclFilePath;
            QFile file(aclFilePath);
            if (file.open(QIODevice::ReadOnly)) {
                QByteArray data = file.readAll();
                file.close();

                QJsonDocument doc = QJsonDocument::fromJson(data);
                QJsonObject root = doc.object();
                QJsonObject users = root.value("users").toObject();

                if (users.contains(username)) {
                    QJsonObject userObj = users.value(username).toObject();
                    QJsonArray projArray = userObj.value("projects").toArray();
                    QSet<QString> allowedUuids;
                    for (int i = 0; i < projArray.size(); ++i) {
                        allowedUuids.insert(projArray.at(i).toString().toLower());
                    }

                    bool isSuperAdmin = allowedUuids.contains("*");

                    qDebug() << "[GUI] Filtering projects for user:" << username << "(Super Admin:" << isSuperAdmin << ")";
                    for (const auto& proj : rawProjects) {
                        std::string stdUuid = boost::lexical_cast<std::string>(proj->getId());
                        QString qUuid = QString::fromStdString(stdUuid).toLower();
                        if (isSuperAdmin || allowedUuids.contains(qUuid)) {
                            Projects.push_back(proj);
                            qDebug() << "[GUI] Access GRANTED for project:" << proj->getName().c_str();
                        } else {
                            qDebug() << "[GUI] Access DENIED for project:" << proj->getName().c_str();
                        }
                    }
                } else {
                    qDebug() << "[GUI] User" << username << "not defined in ACL, allowing NO projects.";
                }
            } else {
                qDebug() << "[GUI] Failed to read users_acl.json, allowing all projects.";
                Projects = rawProjects;
            }
        }

        ProjectViewModel->clearAllElements();
        DigitalTwinMap.clear();
        ProjectViewModel->setProjects(Projects);
        for (const auto& project : Projects) {
            DigitalTwinMap[project->getId()] = BackendCommunication->getAllDigitalTwinsForProjectWithId(project->getId());
            ProjectViewModel->setDigitalTwinForProjectWithId(project, DigitalTwinMap[project->getId()]);
        }
    }
}
