#include "AuthenticationService.h"
#include <BECommunicationService.h>
#include <sysmlv2/rest/entities/Project.h>
#include <iostream>
#include <algorithm>
#include <boost/uuid/uuid_io.hpp>
#include <boost/lexical_cast.hpp>
#include <boost/property_tree/ptree.hpp>
#include <boost/property_tree/json_parser.hpp>

namespace DIGITAL_TWIN_SERVER
{
	AuthenticationService::AuthenticationService()
		: _backendService(nullptr)
	{
	}

	AuthenticationService::AuthenticationService(BACKEND_COMMUNICATION::CommunicationService* backendService)
		: _backendService(backendService)
	{
		loadAclConfig();
	}

	AuthenticationService::~AuthenticationService()
	{
	}

	void AuthenticationService::loadAclConfig() {
		try {
			boost::property_tree::ptree pt;
			// Loading the local ACL file maintained on the broker
			boost::property_tree::read_json("users_acl.json", pt);
			
			for (auto& user : pt.get_child("users")) {
				std::string username = user.first;
				std::vector<std::string> projects;
				for (auto& proj : user.second.get_child("projects")) {
					projects.push_back(proj.second.data());
				}
				_userAcls[username] = projects;
			}
			std::cout << "[AuthService] Loaded ACL config with " << _userAcls.size() << " users.\n";
		} catch (const std::exception& e) {
			std::cerr << "[AuthService] Failed to load ACL config from users_acl.json: " << e.what() << "\n";
		}
	}

	bool AuthenticationService::validateUser(const std::string& username, const std::string& password, Principal& outPrincipal)
	{
		// Reload ACL from disk to allow dynamic updates without restarting the broker
		loadAclConfig();

		if (!_backendService) {
			std::cerr << "[AuthService] No backend service configured — cannot validate user.\n";
			return false;
		}

		try {
			// Step 1: Authenticate against the SysML v2 backend
			bool loginSuccess = _backendService->setUserForLoginInBackend(username, password);
			if (!loginSuccess) {
				std::cout << "[AuthService] Login failed for user: " << username << "\n";
				return false;
			}

			// Step 2: Retrieve projects visible to this authenticated user from LOCAL ACL
			std::vector<std::string> projectIds;
			auto it = _userAcls.find(username);
			if (it != _userAcls.end()) {
				projectIds = it->second;
			} else {
				std::cout << "[AuthService] User " << username << " authenticated but not found in local ACL.\n";
			}

			// A user with no accessible projects has no reason to connect
			if (projectIds.empty()) {
				std::cout << "[AuthService] User " << username << " authenticated but has no projects.\n";
			}

			outPrincipal.id = username;
			outPrincipal.authorizedProjectIds = std::move(projectIds);
			outPrincipal.isPhysicalTwin = false;

			std::cout << "[AuthService] User " << username << " authenticated with "
			          << outPrincipal.authorizedProjectIds.size() << " project(s).\n";
			return true;

		} catch (const std::exception& ex) {
			std::cerr << "[AuthService] Exception during user validation: " << ex.what() << "\n";
			return false;
		}
	}

	bool AuthenticationService::canSubscribe(Principal const& p, std::string_view filter) const
	{
		// System topics (e.g., "connectToTwin") are open to all authenticated users
		if (isSystemTopic(filter)) return true;

		// Extract project UUID from the first segment of the topic filter
		std::string projectId = extractProjectId(filter);
		if (projectId.empty()) return true; // No project prefix → system-level

		// Check if the project is in the principal's authorized set
		return std::find(
			p.authorizedProjectIds.begin(),
			p.authorizedProjectIds.end(),
			projectId
		) != p.authorizedProjectIds.end();
	}

	bool AuthenticationService::canPublish(Principal const& p, std::string_view topic) const
	{
		// System topics are open to all authenticated users
		if (isSystemTopic(topic)) return true;

		std::string projectId = extractProjectId(topic);
		if (projectId.empty()) return true; // No project prefix → system-level

		// For Physical Twins: additionally restrict to device-owned topics
		if (p.isPhysicalTwin) {
			// PT may only publish to topics that begin with its own client ID
			std::string devicePrefix = p.id + "/";
			if (topic.rfind(devicePrefix, 0) != 0) {
				return false;
			}
		}

		// Check project authorization
		return std::find(
			p.authorizedProjectIds.begin(),
			p.authorizedProjectIds.end(),
			projectId
		) != p.authorizedProjectIds.end();
	}

	std::string AuthenticationService::extractProjectId(std::string_view topic)
	{
		// The project UUID is expected as the first segment: "project-uuid/rest/of/topic"
		auto pos = topic.find('/');
		if (pos == std::string_view::npos) {
			// No slash found — this is a flat topic name (system topic)
			return "";
		}
		return std::string(topic.substr(0, pos));
	}

	bool AuthenticationService::isSystemTopic(std::string_view topic)
	{
		// Framework-internal topics that are not project-scoped
		return topic == "connectToTwin"
		    || topic.rfind("$SYS/", 0) == 0;
	}
}
