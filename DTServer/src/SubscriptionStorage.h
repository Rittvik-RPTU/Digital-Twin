#pragma once

#include <mutex>
#include <vector>
#include <memory>
#include <string>

namespace DIGITAL_TWIN_SERVER
{
	class Session;

	struct SubscriptionEntry {
		std::shared_ptr<Session> Session;
		std::string Filter;
		bool NoLocal = false;
	};

	class SubscriptionStorage
	{
	public:
		SubscriptionStorage() = default;
		~SubscriptionStorage() = default;

		void add(std::shared_ptr<Session> session, std::string filter, bool no_local);
		void removeAll(std::shared_ptr<Session> session);
		bool matchFilter(std::string_view filter, std::string_view topic);
		static std::vector<std::string_view>  split(std::string_view s);

		template<class F>
		void forEachMatch(std::string_view topic, std::shared_ptr<Session> publisher, F&& function)
		{
			std::lock_guard lg(Mutex);
			for (auto it = Subscriptions.begin(); it != Subscriptions.end();)
			{
				auto session_lock = it->Session;
				if (!session_lock)
				{
					it = Subscriptions.erase(it);
					continue;
				}
				if (it->NoLocal && session_lock == publisher)
				{
					++it;
					continue;
				}
				if (matchFilter(it->Filter, topic))
					function(session_lock);
				++it;
			}
		}

		void broadcast(std::string topic, std::string payload);
	private:
		std::mutex Mutex;
		std::vector<SubscriptionEntry> Subscriptions;
	};
}
