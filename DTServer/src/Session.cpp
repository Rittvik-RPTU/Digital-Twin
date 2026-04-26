#include "Session.h"

#include <iostream>
#include <async_mqtt/all.hpp>

namespace DIGITAL_TWIN_SERVER
{
    Session::Session(boost::asio::io_context* ioc, SubscriptionStorage &subStore,
                     AuthenticationService &authService) :
        _subscriptionStorage(subStore),
        _authService(authService) {
        ServerEndpoint = new async_mqtt::endpoint<async_mqtt::role::server, async_mqtt::protocol::mqtt>(async_mqtt::protocol_version::v5,ioc->get_executor());
    }

    void Session::start() {
        _subscriptionStorage.add(this,"",false);
        recv_connect();
    }

    void Session::stop() {
        _subscriptionStorage.removeAll(this);
        boost::system::error_code ec;
        ServerEndpoint->lowest_layer().close(ec);
    }

    void Session::recv_connect() {
        auto self = this;
        ServerEndpoint->async_recv([self](async_mqtt::error_code const& ec, std::optional<async_mqtt::packet_variant> pv_opt) {
            if (ec || !pv_opt) return self->stop();

            pv_opt->visit(async_mqtt::overload{
                [&](async_mqtt::v5::connect_packet const& cp) {
                    std::cout << "CONNECT client_id=" << cp.client_id() << "\n";

                    self->ClientId = std::string(cp.client_id());

                    // --- Phase 2: Credential extraction and validation ---

                    // Internal server client is auto-authenticated (trusted)
                    if (self->ClientId == "digital-twin-server") {
                        self->_principal.id = "digital-twin-server";
                        self->_principal.isPhysicalTwin = false;
                        self->_authenticated = true;

                        std::cout << "[Session] Internal client auto-authenticated.\n";

                        async_mqtt::v5::connack_packet ack{false, async_mqtt::connect_reason_code::success};
                        self->ServerEndpoint->async_send(ack, [self](async_mqtt::error_code const& ec2) {
                            if (ec2) return self->stop();
                            self->recv_loop();
                        });
                        return;
                    }

                    // Extract credentials from the CONNECT packet
                    auto opt_username = cp.user_name();
                    auto opt_password = cp.password();

                    if (!opt_username || !opt_password) {
                        std::cout << "[Session] CONNECT rejected: missing credentials from client "
                                  << self->ClientId << "\n";

                        async_mqtt::v5::connack_packet ack{false, async_mqtt::connect_reason_code::not_authorized};
                        self->ServerEndpoint->async_send(ack, [self](async_mqtt::error_code const&) {
                            self->stop();
                        });
                        return;
                    }

                    std::string username(opt_username->begin(), opt_username->end());
                    std::string password(opt_password->begin(), opt_password->end());

                    // Validate credentials against the SysML v2 backend
                    bool authenticated = self->_authService.validateUser(username, password, self->_principal);

                    if (!authenticated) {
                        std::cout << "[Session] CONNECT rejected: invalid credentials for user " << username << "\n";

                        async_mqtt::v5::connack_packet ack{false, async_mqtt::connect_reason_code::not_authorized};
                        self->ServerEndpoint->async_send(ack, [self](async_mqtt::error_code const&) {
                            self->stop();
                        });
                        return;
                    }

                    // Authentication successful
                    self->_authenticated = true;
                    std::cout << "[Session] CONNECT accepted for user " << username << "\n";

                    async_mqtt::v5::connack_packet ack{false, async_mqtt::connect_reason_code::success};
                    self->ServerEndpoint->async_send(ack, [self](async_mqtt::error_code const& ec2) {
                        if (ec2) return self->stop();
                        self->recv_loop();
                    });
                },
                [&](auto const&) {
                    // first packet wasn't CONNECT
                    self->stop();
                }
            });
        });
    }

    void Session::recv_loop() {
        auto self = this;
        ServerEndpoint->async_recv([self](async_mqtt::error_code const& ec, std::optional<async_mqtt::packet_variant> pv_opt) {
            if (ec || !pv_opt) return self->stop();

            pv_opt->visit(async_mqtt::overload{
                [&](async_mqtt::v5::pingreq_packet const&) {
                    async_mqtt::v5::pingresp_packet resp;
                    self->ServerEndpoint->async_send(resp, [](async_mqtt::error_code const&) {});
                },
                [&](async_mqtt::v5::subscribe_packet const& sp) {
                    // --- Phase 2: Per-topic access control on SUBSCRIBE ---
                    std::vector<async_mqtt::suback_reason_code> reasons;
                    reasons.reserve(sp.entries().size());

                    for (const auto& entry : sp.entries()) {
                        std::string filter(entry.topic());

                        if (self->_authService.canSubscribe(self->_principal, filter)) {
                            reasons.push_back(async_mqtt::suback_reason_code::granted_qos_0);
                            // Only add authorized subscriptions to the storage
                            self->_subscriptionStorage.add(self, filter, false);
                        } else {
                            std::cout << "[Session] SUBSCRIBE denied: " << self->_principal.id
                                      << " cannot subscribe to " << filter << "\n";
                            reasons.push_back(async_mqtt::suback_reason_code::not_authorized);
                        }
                    }

                    async_mqtt::v5::suback_packet ack{sp.packet_id(), reasons};
                    self->ServerEndpoint->async_send(ack, [](async_mqtt::error_code const&) {});
                },
                [&](async_mqtt::v5::publish_packet const& pp) {
                    // QoS0-only
                    if (pp.opts().get_qos() != async_mqtt::qos::at_most_once) {
                        async_mqtt::v5::disconnect_packet dp{
                            async_mqtt::disconnect_reason_code::protocol_error
                        };
                        self->ServerEndpoint->async_send(dp, [self](async_mqtt::error_code const&) { self->stop(); });
                        return;
                    }

                    std::string topic = std::string(pp.topic());
                    std::string payload {pp.payload().data(),pp.payload().size()};

                    // --- Phase 2: Per-topic access control on PUBLISH ---
                    if (!self->_authService.canPublish(self->_principal, topic)) {
                        std::cout << "[Session] PUBLISH denied: " << self->_principal.id
                                  << " cannot publish to " << topic << "\n";

                        async_mqtt::v5::disconnect_packet dp{
                            async_mqtt::disconnect_reason_code::not_authorized
                        };
                        self->ServerEndpoint->async_send(dp, [self](async_mqtt::error_code const&) { self->stop(); });
                        return;
                    }

                    std::cout << "PUBLISH topic=" << topic
                              << " payload_bytes=" << payload.size() << "\n";

                    self->_subscriptionStorage.broadcast(topic, payload);
                },
                [&](async_mqtt::v5::disconnect_packet const&) {
                    self->stop();
                },
                [&](auto const&) {
                    // ignore other packets for minimal broker
                }
            });

            self->recv_loop(); // next receive
        });
    }

    void Session::send_qos0_publish(std::string const& topic, std::string const& payload) {
        async_mqtt::v5::publish_packet out{
            topic,
            payload,
            async_mqtt::qos::at_most_once
        };
        ServerEndpoint->async_send(out, [](async_mqtt::error_code const&) {});
    }

    boost::asio::ip::tcp::socket::lowest_layer_type & Session::lowest_layer() {
        return ServerEndpoint->lowest_layer();
    }

    bool Session::operator==(const Session &other) const {
        return ClientId==other.ClientId;
    }
}
