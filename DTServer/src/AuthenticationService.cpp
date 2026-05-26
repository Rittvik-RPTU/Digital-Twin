#include "AuthenticationService.h"
#include <BECommunicationService.h>
#include <sysmlv2/rest/entities/Project.h>
#include <sysmlv2/rest/entities/Branch.h>
#include <sysmlv2/rest/entities/Commit.h>
#include <kerml/root/elements/Element.h>
#include <iostream>
#include <sstream>
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
		loadLocalBoundsConfig();
	}

	AuthenticationService::~AuthenticationService()
	{
	}

	void AuthenticationService::loadAclConfig() {
		std::lock_guard<std::recursive_mutex> lock(_authMutex);
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

	void AuthenticationService::loadLocalBoundsConfig() {
		std::lock_guard<std::recursive_mutex> lock(_authMutex);
		try {
			boost::property_tree::ptree pt;
			// Load local bounds configuration for projects without backend-defined bounds
			boost::property_tree::read_json("project_bounds.json", pt);

			for (auto& projectEntry : pt.get_child("projects")) {
				std::string projectId = projectEntry.first;
				std::map<std::string, ModelBounds> projectBounds;

				for (auto& boundEntry : projectEntry.second) {
					std::string attrName = boundEntry.first;
					double minVal = boundEntry.second.get<double>("min");
					double maxVal = boundEntry.second.get<double>("max");
					projectBounds[attrName] = ModelBounds{ minVal, maxVal };
				}

				if (!projectBounds.empty()) {
					_boundsCache[projectId] = std::move(projectBounds);
					std::cout << "[AuthService][Bounds] Loaded " << _boundsCache[projectId].size()
					          << " local bounds for project " << projectId << "\n";
				}
			}
		} catch (const std::exception& e) {
			std::cout << "[AuthService][Bounds] No local bounds config (project_bounds.json): "
			          << e.what() << " — will use backend bounds or fail-open.\n";
		}
	}

	bool AuthenticationService::isAttributeUsageElement(const boost::property_tree::ptree& elementJson) {
		// Check standard @type field
		auto type = elementJson.get_optional<std::string>("@type");
		if (type) {
			// Handle variations: "AttributeUsage", "sysml:AttributeUsage", etc.
			if (type->find("AttributeUsage") != std::string::npos) {
				return true;
			}
		}

		// Check kind field
		auto kind = elementJson.get_optional<std::string>("kind");
		if (kind) {
			if (kind->find("AttributeUsage") != std::string::npos ||
			    kind->find("attribute") != std::string::npos) {
				return true;
			}
		}

		return false;
	}

	boost::optional<std::string> AuthenticationService::extractElementName(
		const boost::property_tree::ptree& elementJson) {

		// Try declaredName first (most common in SysML v2)
		auto declaredName = elementJson.get_optional<std::string>("declaredName");
		if (declaredName && !declaredName->empty()) {
			return *declaredName;
		}

		// Try name field
		auto name = elementJson.get_optional<std::string>("name");
		if (name && !name->empty()) {
			return *name;
		}

		// Try extracting from @id as last resort
		auto id = elementJson.get_optional<std::string>("@id");
		if (id && !id->empty()) {
			// Extract last segment after '-'
			size_t lastDash = id->rfind('-');
			if (lastDash != std::string::npos && lastDash < id->length() - 1) {
				return id->substr(lastDash + 1);
			}
		}

		return boost::optional<std::string>();
	}

	boost::optional<AuthenticationService::ModelBounds> AuthenticationService::extractBoundsFromElement(
		const boost::property_tree::ptree& elementJson,
		const std::string& elementName) {

		double minVal = -1.0, maxVal = -1.0;
		bool found = false;

		// Strategy 1: Standard SysML v2 bounds (lowerBound/upperBound)
		auto lowerBound = elementJson.get_optional<double>("lowerBound");
		auto upperBound = elementJson.get_optional<double>("upperBound");
		if (lowerBound && upperBound) {
			minVal = *lowerBound;
			maxVal = *upperBound;
			found = true;
			std::cout << "[AuthService][Bounds][DEBUG] Found standard bounds for '" << elementName
			          << "': [" << minVal << ", " << maxVal << "]\n";
		}

		// Strategy 2: Alternate naming (min/max)
		if (!found) {
			auto min = elementJson.get_optional<double>("min");
			auto max = elementJson.get_optional<double>("max");
			if (min && max) {
				minVal = *min;
				maxVal = *max;
				found = true;
				std::cout << "[AuthService][Bounds][DEBUG] Found min/max bounds for '" << elementName
				          << "': [" << minVal << ", " << maxVal << "]\n";
			}
		}

		// Strategy 3: Alternate naming (low/high)
		if (!found) {
			auto low = elementJson.get_optional<double>("low");
			auto high = elementJson.get_optional<double>("high");
			if (low && high) {
				minVal = *low;
				maxVal = *high;
				found = true;
				std::cout << "[AuthService][Bounds][DEBUG] Found low/high bounds for '" << elementName
				          << "': [" << minVal << ", " << maxVal << "]\n";
			}
		}

		// Strategy 4: Nested constraints object
		if (!found) {
			auto constraints = elementJson.get_child_optional("constraints");
			if (constraints) {
				auto min = constraints->get_optional<double>("min");
				auto max = constraints->get_optional<double>("max");
				if (min && max) {
					minVal = *min;
					maxVal = *max;
					found = true;
					std::cout << "[AuthService][Bounds][DEBUG] Found nested bounds for '" << elementName
					          << "': [" << minVal << ", " << maxVal << "]\n";
				}
				// Also try lowerBound/upperBound in constraints
				if (!found) {
					auto lBound = constraints->get_optional<double>("lowerBound");
					auto uBound = constraints->get_optional<double>("upperBound");
					if (lBound && uBound) {
						minVal = *lBound;
						maxVal = *uBound;
						found = true;
						std::cout << "[AuthService][Bounds][DEBUG] Found nested standard bounds for '" << elementName
						          << "': [" << minVal << ", " << maxVal << "]\n";
					}
				}
			}
		}

		if (found) {
			return ModelBounds{ minVal, maxVal };
		}

		return boost::optional<ModelBounds>();
	}

	bool AuthenticationService::validateUser(const std::string& username, const std::string& password, Principal& outPrincipal)
	{
		std::lock_guard<std::recursive_mutex> lock(_authMutex);
		// Reload ACL from disk to allow dynamic updates without restarting the broker
		loadAclConfig();

		if (!_backendService) {
			std::cerr << "[AuthService] No backend service configured — cannot validate user.\n";
			return false;
		}

		try {
			// Phase 3: Physical Twin API Key Authentication
			if (username == "PHYSICAL_TWIN") {
				// The password field contains the API Key
				return _apiKeyStore.validateApiKey(password, outPrincipal);
			}

			// Step 1: Verify identity against the SysML v2 backend.
			// We call getAccessibleProjectIds which internally logs in and calls GET /projects.
			// NOTE: The reference SysML v2 backend has a known gap — it returns ALL projects
			// globally regardless of the authenticated user. Therefore, we use the backend
			// strictly for IDENTITY VERIFICATION (login success/failure) and discard its project list.
			std::vector<boost::uuids::uuid> backendProjects = _backendService->getAccessibleProjectIds(username, password);
			if (backendProjects.empty()) {
				// A completely empty result means the login itself failed (401 Unauthorized).
				std::cout << "[AuthService] Identity verification failed for user: " << username << "\n";
				return false;
			}

			// Step 2: Enforce authorization using the local ACL (users_acl.json).
			// This compensates for the SysML v2 backend's lack of user-scoped project filtering.
			// This is the documented "Hybrid Two-Step Validation" strategy.
			auto aclIt = _userAcls.find(username);
			if (aclIt == _userAcls.end()) {
				std::cout << "[AuthService] User '" << username
				          << "' authenticated on backend but has no local ACL entry. Access denied.\n";
				return false;
			}

			outPrincipal.id = username;
			outPrincipal.authorizedProjectIds = aclIt->second;
			outPrincipal.isPhysicalTwin = false;

			std::cout << "[AuthService] User " << username << " authenticated (Hybrid) with "
			          << outPrincipal.authorizedProjectIds.size() << " ACL-scoped project(s).\n";
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

		// Wildcard check for super-admin access
		if (std::find(p.authorizedProjectIds.begin(), p.authorizedProjectIds.end(), "*") != p.authorizedProjectIds.end()) {
			return true;
		}

		// Check if the project is in the principal's authorized set
		return std::find(
			p.authorizedProjectIds.begin(),
			p.authorizedProjectIds.end(),
			projectId
		) != p.authorizedProjectIds.end();
	}

	bool AuthenticationService::canPublish(Principal const& p, std::string_view topic) const
	{
		// Critical: Only the internal server can publish to the integrity heartbeat topic
		if (topic == "dt/system/integrity" && p.id != "digital-twin-server") {
			return false;
		}

		// Other system topics are open to all authenticated users
		if (isSystemTopic(topic)) return true;

		std::string projectId = extractProjectId(topic);
		if (projectId.empty()) return true; // No project prefix → system-level

		// Wildcard check for super-admin access
		if (std::find(p.authorizedProjectIds.begin(), p.authorizedProjectIds.end(), "*") != p.authorizedProjectIds.end()) {
			return true;
		}

		// For Physical Twins: additionally restrict to device-owned topics
		if (p.isPhysicalTwin) {
			// PT may only publish to topics within its project that begin with its own device ID
			// Expected format: "project-uuid/device-id/..."
			std::string expectedPrefix = projectId + "/" + p.id + "/";
			if (topic.rfind(expectedPrefix, 0) != 0) {
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
		if (topic == "connectToTwin") return true;
		if (topic.size() >= 3 && topic.substr(0, 3) == "dt/") return true;
		if (topic.size() >= 5 && topic.substr(0, 5) == "$SYS/") return true;
		return false;
	}

	void AuthenticationService::fetchBoundsFromModel(const std::string& projectId)
	{
		std::lock_guard<std::recursive_mutex> lock(_authMutex);

		// Check if already loaded from local config
		if (_boundsCache.find(projectId) != _boundsCache.end() && !_boundsCache[projectId].empty()) {
			std::cout << "[AuthService][Bounds] Using pre-loaded local bounds for project " << projectId << "\n";
			return;
		}

		if (!_backendService) {
			std::cerr << "[AuthService][Bounds] No backend service configured — cannot fetch bounds from model.\n";
			return;
		}

		try {
			std::cout << "[AuthService][Bounds] Fetching bounds from SysML v2 backend for project " << projectId << "\n";

			boost::uuids::uuid projUuid = boost::lexical_cast<boost::uuids::uuid>(projectId);

			// 1. Get default branch (first branch = main)
			auto branches = _backendService->getAllBranchesForProjectWithID(projUuid);
			if (branches.empty()) {
				std::cerr << "[AuthService][Bounds] No branches found for project " << projectId << "\n";
				return;
			}

			// 2. Get the head commit of the default branch
			auto headCommit = branches.front()->getHead();
			if (!headCommit) {
				std::cerr << "[AuthService][Bounds] No head commit for project " << projectId << "\n";
				return;
			}
			boost::uuids::uuid commitUuid = headCommit->getId();

			// 3. Fetch all elements of the latest commit
			auto elements = _backendService->getAllElementsOfCommit(projUuid, commitUuid);
			std::cout << "[AuthService][Bounds][DEBUG] Retrieved " << elements.size()
			          << " elements from commit " << boost::uuids::to_string(commitUuid) << "\n";

			// 4. Parse each element's JSON to find AttributeUsage constraints
			std::map<std::string, ModelBounds> projectBounds;
			int attributeCount = 0;

			for (auto const& elem : elements) {
				if (!elem) continue;

				try {
					std::string json = elem->serializeToJson();
					std::cout << "[AuthService][Bounds][DEBUG] Element JSON: " << json.substr(0, 200)
					          << (json.length() > 200 ? "..." : "") << "\n";

					boost::property_tree::ptree pt;
					std::istringstream ss(json);
					boost::property_tree::read_json(ss, pt);

					// Check if this is an AttributeUsage element (handles multiple schema variants)
					if (!isAttributeUsageElement(pt)) {
						continue;
					}

					attributeCount++;

					// Extract element name (handles multiple property name variants)
					auto elemName = extractElementName(pt);
					if (!elemName) {
						std::cout << "[AuthService][Bounds][DEBUG] Could not extract name for attribute element\n";
						continue;
					}

					// Extract bounds (handles multiple naming conventions and nested structures)
					auto bounds = extractBoundsFromElement(pt, *elemName);
					if (!bounds) {
						std::cout << "[AuthService][Bounds][DEBUG] No bounds found for attribute '" << *elemName << "'\n";
						continue;
					}

					projectBounds[*elemName] = *bounds;
					std::cout << "[AuthService][Bounds] ✓ Loaded constraint '" << *elemName
					          << "' [" << bounds->min << ", " << bounds->max << "]\n";

				} catch (const std::exception& ex) {
					std::cout << "[AuthService][Bounds][DEBUG] Skipped element: " << ex.what() << "\n";
				}
			}

			// Store in cache
			_boundsCache[projectId] = std::move(projectBounds);
			std::cout << "[AuthService][Bounds] ✓ Successfully cached " << _boundsCache[projectId].size()
			          << " constraint(s) from " << attributeCount << " attributes for project "
			          << projectId << "\n";

		} catch (const boost::bad_lexical_cast& ex) {
			std::cerr << "[AuthService][Bounds] Invalid project UUID: " << projectId << "\n";
		} catch (const std::exception& ex) {
			std::cerr << "[AuthService][Bounds] ✗ Failed to fetch bounds for project " << projectId
			          << ": " << ex.what() << "\n";
		}
	}

	bool AuthenticationService::verifyPayload(const std::string& projectId,
	                                          const std::string& topic,
	                                          const std::string& payload)
	{
		std::lock_guard<std::recursive_mutex> lock(_authMutex);

		// Lazily fetch bounds if not yet cached for this project
		if (_boundsCache.find(projectId) == _boundsCache.end()) {
			fetchBoundsFromModel(projectId);
		}

		// If no bounds defined for this project, log warning (non-blocking)
		auto projIt = _boundsCache.find(projectId);
		if (projIt == _boundsCache.end() || projIt->second.empty()) {
			std::cout << "[AuthService][Bounds] ⚠ WARNING: No bounds cached for project " << projectId
			          << " — payload validation DISABLED (Layer A bypass).\n";
			return true;  // Non-blocking: allow payload through but flag the issue
		}

		const auto& bounds = projIt->second;

		try {
			boost::property_tree::ptree pt;
			std::istringstream ss(payload);
			boost::property_tree::read_json(ss, pt);

			std::cout << "[AuthService][Bounds][DEBUG] Validating payload on topic '" << topic
			          << "' against " << bounds.size() << " constraint(s)\n";

			int violationCount = 0;

			for (auto const& [key, value] : pt) {
				auto boundIt = bounds.find(key);
				if (boundIt == bounds.end()) {
					// No bound defined for this attribute — allow it
					std::cout << "[AuthService][Bounds][DEBUG] No constraint for attribute '" << key << "' — allowed\n";
					continue;
				}

				double v = value.get_value<double>();
				const ModelBounds& b = boundIt->second;

				std::cout << "[AuthService][Bounds][DEBUG] Checking '" << key << "' = " << v
				          << " against [" << b.min << ", " << b.max << "]... ";

				if (v < b.min || v > b.max) {
					std::cerr << "VIOLATION!\n";
					std::cerr << "[SECURITY ALERT][Layer A] Payload violation on topic '" << topic
					          << "': attribute '" << key << "' = " << v
					          << " violates bounds [" << b.min << ", " << b.max << "]\n";
					violationCount++;
				} else {
					std::cout << "OK\n";
				}
			}

			if (violationCount > 0) {
				std::cerr << "[SECURITY ALERT][Layer A] ✗ Rejecting payload: " << violationCount
				          << " constraint(s) violated\n";
				return false;  // Reject payload
			}

			std::cout << "[AuthService][Bounds] ✓ Payload validation passed for topic '" << topic << "'\n";
			return true;  // Accept payload

		} catch (const std::exception& ex) {
			// Non-JSON payload: cannot verify bounds, but don't reject it
			std::cout << "[AuthService][Bounds] Non-JSON payload on topic '" << topic
			          << "' — skipping bounds validation: " << ex.what() << "\n";
			return true;  // Allow non-JSON payloads through
		}
	}
} // namespace DIGITAL_TWIN_SERVER
