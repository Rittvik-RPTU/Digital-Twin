//
// Created by Moritz Herzog on 25.02.26.
//

#pragma once

#include <string>
#include <sysmlv2/rest/entities/Commit.h>
#include <sysmlv2/rest/entities/IEntity.h>

#include "../cpp_backend_communication_global.h"

namespace SysMLv2::REST {
    class CPSBACKENDCOMMUNICATION_EXPORT TwinRequest : public IEntity{
    public:
        explicit TwinRequest(std::string name, std::shared_ptr<SysMLv2::REST::Commit> referencedCommit);
        explicit TwinRequest(std::string jsonString);
        virtual ~TwinRequest() = default;

        std::string serializeToJson() override;

        std::string name();
        std::shared_ptr<SysMLv2::REST::Commit> referencedCommit();
    protected:
        void deserializeAndPopulate(const std::string &jsonString) override;

    private:
        std::string Name;
        std::string Type;
        std::shared_ptr<SysMLv2::REST::Commit> ReferencedCommit;
    };
} // SysMLv2::REST
