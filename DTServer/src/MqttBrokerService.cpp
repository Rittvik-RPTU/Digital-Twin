//
// Created by Moritz Herzog on 06.08.24.
//

#include <boost/asio.hpp>
#include <boost/optional.hpp>
#include <boost/asio/recycling_allocator.hpp>
#include <memory>

#include "MqttBrokerService.h"

#include <async_mqtt/all.hpp>
#include <BECommunicationService.h>

#include "Session.h"
#include "SubscriptionStorage.h"

namespace DIGITAL_TWIN_SERVER {

    MQTTBrokerService::MQTTBrokerService(boost::asio::io_context* ioc, unsigned serverPort,
                                         BACKEND_COMMUNICATION::CommunicationService* backendService,
                                         std::string serverCertPath, std::string serverCertPrivKeyPath) :
    Context(ioc),
    Acceptor(*ioc,boost::asio::ip::tcp::endpoint(boost::asio::ip::tcp::v4(), serverPort)),
    HeartbeatTimer(*ioc),
    authService(backendService)
    {
        ServerPort = serverPort;
        assert(!(!serverCertPath.empty() && serverCertPrivKeyPath.empty()));
        ServerCertPath = serverCertPath;
        ServerCertPrivKeyPath = serverCertPrivKeyPath;
    }

    MQTTBrokerService::MQTTBrokerService(boost::asio::io_context* ioc, std::string serverCertPath, std::string serverCertPrivKeyPath):
    Context(ioc),
    Acceptor(*ioc,boost::asio::ip::tcp::endpoint(boost::asio::ip::tcp::v4(), 1883)),
    HeartbeatTimer(*ioc)
    {
        assert(!(!serverCertPath.empty() && serverCertPrivKeyPath.empty()));
        ServerCertPath = serverCertPath;
        ServerCertPrivKeyPath = serverCertPrivKeyPath;
    }

    void MQTTBrokerService::setUpTLS()
    {
    }

    void MQTTBrokerService::run()
    {
        startHeartbeat();
        accept_one();
        Context->run();
    }

    void MQTTBrokerService::accept_one() {
        auto s = std::make_shared<Session>(Context, _subscriptionStorage, authService);
        Acceptor.async_accept(s->lowest_layer(), [this, s](boost::system::error_code ec) {
            if (!ec) s->start();
            accept_one();
        });
    }

    void MQTTBrokerService::startHeartbeat() {
        HeartbeatTimer.expires_after(std::chrono::seconds(10));
        HeartbeatTimer.async_wait([this](boost::system::error_code ec) {
            if (!ec) {
                // Periodically publish a signed integrity token
                // In a production system, this would be a hash of the binary signed by a TPM/HSM
                std::string payload = "{\"status\":\"ok\", \"integrity_token\":\"MASTER_THESIS_SECURE_DT\"}";
                
                _subscriptionStorage.forEachMatch("dt/system/integrity", nullptr, [&](std::shared_ptr<Session> s) {
                    s->send_qos0_publish("dt/system/integrity", payload);
                });

                startHeartbeat();
            }
        });
    }
}
