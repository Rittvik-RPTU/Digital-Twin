//
// Created by Moritz Herzog on 03.01.25.
//

#ifndef DIGITALTWIN_UPLOADPROJECTFILETOBACKEND_H
#define DIGITALTWIN_UPLOADPROJECTFILETOBACKEND_H

#include <QMainWindow>
#include <QStandardItemModel>
#include "../Models/Markdown/MarkdownParser.h"
#include <vector>
#include <kerml/root/elements/Element.h>
#include <sysmlv2/rest/entities/Commit.h>
#include <sysmlv2/rest/entities/Project.h>
#include <BECommunicationService.h>

namespace PHYSICAL_TWIN_COMMUNICATION {
    class MqttClientService;
}

namespace DigitalTwin::Client {
    namespace Ui {
        class UploadProjectFileToBackend;
    }
}

namespace DigitalTwin::Client {
    class UploadProjectFileToBackend : public QMainWindow {
        Q_OBJECT

        enum UploadProjectFileToBackendStatus {
            DocumentOpened,
            OnlineProjectOpened
        };

    public:
        explicit UploadProjectFileToBackend(BACKEND_COMMUNICATION::CommunicationService* service,
                                            PHYSICAL_TWIN_COMMUNICATION::MqttClientService* mqttService,
                                            const std::string& username,
                                            QWidget* parent = NULL);
        ~UploadProjectFileToBackend() override;

        void setElementsForView(std::vector<std::shared_ptr<KerML::Entities::Element>> elements, std::shared_ptr<SysMLv2::REST::Commit> commit, std::shared_ptr<SysMLv2::REST::Project> project);
        void setHTMLTextForView(QString htmlText);

    private slots:
        void onTextEdited();
        void onCreateDigitalTwinClicked();

    private:
        void makeConnections();
        void setMarkdownOfOnlineProject(QString Markdown);
        void setCodeElements();
        void createOnlineProject();
        void redecorateWithStatusChange();

        std::vector<std::shared_ptr<KerML::Entities::Element>> Elements;
        Ui::UploadProjectFileToBackend* Ui;
        MarkdownParser* Parser;
        QStandardItemModel* DTElementsModels;
        BACKEND_COMMUNICATION::CommunicationService* CommunicationService;

        std::shared_ptr<SysMLv2::REST::Commit> Commit;
        std::shared_ptr<SysMLv2::REST::Project> Project;

        UploadProjectFileToBackendStatus Status;

        PHYSICAL_TWIN_COMMUNICATION::MqttClientService* MqttService;
        std::string Username;
    };
}

#endif //DIGITALTWIN_UPLOADPROJECTFILETOBACKEND_H
