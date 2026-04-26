#pragma once

#include <string>
#include <vector>
#include <map>

// Forward declaration to avoid circular includes
namespace BACKEND_COMMUNICATION {
	class CommunicationService;
}

namespace DIGITAL_TWIN_SERVER
{
	/**
	 * Represents an authenticated identity within the broker.
	 * Populated after successful credential validation.
	 */
	struct Principal
	{
		std::string id;
		std::vector<std::string> authorizedProjectIds;
		bool isPhysicalTwin = false;
	};

	/**
	 * Validates user credentials against the SysML v2 backend and enforces
	 * project-based access control on MQTT topics.
	 *
	 * @author Moritz Herzog <herzogm@rptu.de> (original skeleton)
	 * @author Rittvik Vashishtha (Phase 2: credential validation & access control)
	 * @version 2.0
	 */
	class AuthenticationService
	{
	public:
		/**
		 * Default constructor for backward compatibility (no backend validation).
		 */
		AuthenticationService();

		/**
		 * Constructor with backend service for credential validation.
		 * @param backendService Pointer to the SysML v2 REST communication service.
		 */
		explicit AuthenticationService(BACKEND_COMMUNICATION::CommunicationService* backendService);

		~AuthenticationService();

		/**
		 * Validates user credentials against the SysML v2 backend.
		 * On success, populates outPrincipal with the user's identity and
		 * the list of project UUIDs they are authorized to access.
		 *
		 * @param username The SysML v2 backend username.
		 * @param password The SysML v2 backend password.
		 * @param outPrincipal Output parameter populated on successful validation.
		 * @return true if credentials are valid and at least one project is accessible.
		 */
		bool validateUser(const std::string& username, const std::string& password, Principal& outPrincipal);

		/**
		 * Checks whether the given principal is allowed to subscribe to the topic filter.
		 * System-level topics are allowed for all authenticated users.
		 * Project-scoped topics require the project UUID to be in the principal's authorized list.
		 */
		bool canSubscribe(Principal const& p, std::string_view filter) const;

		/**
		 * Checks whether the given principal is allowed to publish to the topic.
		 * Same project-based check as canSubscribe. Physical Twins are additionally
		 * restricted to their own device topic namespace.
		 */
		bool canPublish(Principal const& p, std::string_view topic) const;

	private:
		BACKEND_COMMUNICATION::CommunicationService* _backendService = nullptr;
		std::map<std::string, std::vector<std::string>> _userAcls;
		
		struct DeviceConfig {
			std::string deviceId;
			std::string projectId;
		};
		// Maps API keys to device configurations
		std::map<std::string, DeviceConfig> _deviceAcls;

		void loadAclConfig();

		/**
		 * Extracts the first path segment from a topic string, which is expected
		 * to be a project UUID for project-scoped topics.
		 */
		static std::string extractProjectId(std::string_view topic);

		/**
		 * Returns true if the topic is a framework-internal system topic
		 * (e.g., "connectToTwin") that all authenticated users may access.
		 */
		static bool isSystemTopic(std::string_view topic);
	};
}