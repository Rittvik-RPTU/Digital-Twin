//
// Created by Moritz Herzog on 13.12.23.
//
//---------------------------------------------------------
// Constants, Definitions, Pragmas
//---------------------------------------------------------

//---------------------------------------------------------
// External Classes
//---------------------------------------------------------
#include <utility>
#include <sysmlv2/rest/entities/IEntity.h>
#include <sysmlv2/rest/entities/Project.h>
#include <sysmlv2/rest/entities/Commit.h>
#include <sysmlv2/rest/entities/Branch.h>
#include <kerml/root/elements/Element.h>
#include <boost/uuid/uuid_io.hpp>
#include <boost/lexical_cast.hpp>
#include <sysmlv2/service/online/SysMLAPIImplementation.h>

//---------------------------------------------------------
// Internal Classes
//---------------------------------------------------------
#include "BECommunicationService.h"

#include <nlohmann/json.hpp>
#include <sysmlv2/service/online/SysMLAPIImplementation.h>
#include <sysmlv2/rest/entities/CommitRequest.h>
#include <sysmlv2/rest/entities/ProjectRequest.h>

#include "entities/DigitalTwin.h"


namespace BACKEND_COMMUNICATION {
    CommunicationService::CommunicationService(std::string serverAddress, unsigned int port, std::string serverFolder) :
            Entry_URI(serverFolder),
            ServerAddress(serverAddress),
            Port(port)
    {
        if(Port==443)
            REST_Protocol="https://";

        if ((Port!=443)&&(Port!=80))
            APIImplementation = new SysMLv2::API::SysMLAPIImplementation(REST_Protocol + ServerAddress + ":" + std::to_string(Port) + "/");
        else
            APIImplementation = new SysMLv2::API::SysMLAPIImplementation(REST_Protocol + ServerAddress);

    }

    CommunicationService::CommunicationService(std::string serverAddress, std::string serverFolder) {
        ServerAddress = std::move(serverAddress);
        Entry_URI = std::move(serverFolder);
    }

    std::vector<std::shared_ptr<KerML::Entities::Element>> CommunicationService::getAllElements(boost::uuids::uuid commitId, boost::uuids::uuid projectId) {
        auto entities = APIImplementation->getAllElementsFromCommit(boost::lexical_cast<std::string>(projectId),boost::lexical_cast<std::string>(commitId), BarrierString);
        std::vector<std::shared_ptr<KerML::Entities::Element>> elements;

        for(auto entitiy : entities)
            elements.push_back(dynamic_pointer_cast<KerML::Entities::Element>(entitiy));

        return elements;
    }

    std::vector<std::shared_ptr<SysMLv2::REST::Project>> CommunicationService::getAllProjects() {
        auto projects = APIImplementation->getAllProjects(BarrierString);
        std::vector<std::shared_ptr<SysMLv2::REST::Project>> returnValue;

        for(auto oldProject : projects)
            returnValue.push_back(dynamic_pointer_cast<SysMLv2::REST::Project>(oldProject));

        return returnValue;
    }

    std::shared_ptr<SysMLv2::REST::DigitalTwin> CommunicationService::getDigitalTwinWithID(boost::uuids::uuid , boost::uuids::uuid ) {
        return nullptr;
    }

    std::vector<std::shared_ptr<SysMLv2::REST::DigitalTwin>> CommunicationService::getAllDigitalTwinsForProjectWithId(boost::uuids::uuid projectId) {
        auto twinString = APIImplementation->getCustomRequest("projects/" + boost::lexical_cast<std::string>(projectId) + "/twins",BarrierString);
        std::vector<std::shared_ptr<SysMLv2::REST::DigitalTwin>> returnValue;
        nlohmann::json json = nlohmann::json::parse(twinString);
        std::vector<nlohmann::json> arrayValues = json.get<std::vector<nlohmann::json>>();
        returnValue.reserve(arrayValues.size());
        for(const nlohmann::json& elem : arrayValues) {
            returnValue.emplace_back(std::make_shared<SysMLv2::REST::DigitalTwin>(elem.dump()));
        }
        return returnValue;
    }


    std::shared_ptr<SysMLv2::REST::Commit> CommunicationService::getCommitWithId(boost::uuids::uuid , boost::uuids::uuid ) {
        return nullptr;
    }

    std::shared_ptr<SysMLv2::REST::Commit> CommunicationService::postCommitWithId(boost::uuids::uuid projectId,
                                                                                      std::shared_ptr<SysMLv2::REST::CommitRequest> commit)
    {
        auto commi = APIImplementation->postCommit(boost::lexical_cast<std::string>(projectId), commit, BarrierString);

        std::shared_ptr<SysMLv2::REST::Commit> returnValue = dynamic_pointer_cast<SysMLv2::REST::Commit>(commi);
        return returnValue;
    }


    bool CommunicationService::setUserForLoginInBackend(std::string username, std::string password) {
        BarrierString = APIImplementation->loginUserWithPassword(username,password);
        return !BarrierString.empty();
    }

    std::shared_ptr<SysMLv2::REST::DigitalTwin> CommunicationService::postDigitalTwin(std::shared_ptr<SysMLv2::REST::TwinRequest> digitalTwin,
	    boost::uuids::uuid projectId)
    {
        auto digitalT = APIImplementation->postCustomRequest("projects/" + boost::lexical_cast<std::string>(projectId) + "/twins", digitalTwin->serializeToJson(), BarrierString);

        auto returnValue = std::make_shared<SysMLv2::REST::DigitalTwin>(digitalT);
        return returnValue;
    }

    std::vector<std::shared_ptr<SysMLv2::REST::Branch>> CommunicationService::getAllBranchesForProjectWithID(boost::uuids::uuid projectId) {
        auto elements = APIImplementation->getAllBranchesFroProject(boost::lexical_cast<std::string>(projectId), BarrierString);

        std::vector<std::shared_ptr<SysMLv2::REST::Branch>> returnValue;

        for (auto elem : elements)
            returnValue.push_back(dynamic_pointer_cast<SysMLv2::REST::Branch>(elem));

        return returnValue;
    }

    std::vector<boost::uuids::uuid> CommunicationService::getAccessibleProjectIds(const std::string& username, const std::string& password) {
        std::string barrier;
        SysMLv2::API::SysMLAPIImplementation* tempApi;
        if ((Port!=443)&&(Port!=80))
            tempApi = new SysMLv2::API::SysMLAPIImplementation(REST_Protocol + ServerAddress + ":" + std::to_string(Port) + "/");
        else
            tempApi = new SysMLv2::API::SysMLAPIImplementation(REST_Protocol + ServerAddress);
            
        barrier = tempApi->loginUserWithPassword(username, password);
        if (barrier.empty()) {
            delete tempApi;
            return {};
        }
        
        auto projects = tempApi->getAllProjects(barrier);
        std::vector<boost::uuids::uuid> projectIds;
        for (auto proj : projects) {
            auto restProj = std::dynamic_pointer_cast<SysMLv2::REST::Project>(proj);
            if (restProj) {
                projectIds.push_back(restProj->getId());
            }
        }
        delete tempApi;
        return projectIds;
    }


    std::vector<std::shared_ptr<KerML::Entities::Element>>
    CommunicationService::getAllElementsOfCommit(boost::uuids::uuid projectId, boost::uuids::uuid commitId) {
        auto elements = APIImplementation->getAllElementsFromCommit(boost::lexical_cast<std::string>(projectId),boost::lexical_cast<std::string>(commitId), BarrierString);
        std::vector<std::shared_ptr<KerML::Entities::Element>> returnValue;

        for(auto elem : elements)
            returnValue.push_back(dynamic_pointer_cast<KerML::Entities::Element>(elem));

        return returnValue;
    }

    std::shared_ptr<SysMLv2::REST::Project>
    CommunicationService::postProject(std::string projectName, std::string projectDescription, std::string defaultBranchName) {
        auto projectRequest = std::make_shared<SysMLv2::REST::ProjectRequest>(projectName,projectDescription, defaultBranchName);
        auto project = std::dynamic_pointer_cast<SysMLv2::REST::Project>(APIImplementation->postProject(projectRequest, BarrierString));
        return project;
    }


}
