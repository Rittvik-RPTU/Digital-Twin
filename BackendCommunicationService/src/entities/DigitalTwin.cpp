//
// Created by Moritz Herzog on 22.07.25.
//

#include <nlohmann/json.hpp>
#include <sysmlv2/rest/entities/JSONEntities.h>
#include <boost/uuid/uuid.hpp>
#include <boost/uuid/string_generator.hpp>
#include <boost/uuid/uuid_io.hpp>
#include <boost/uuid/random_generator.hpp>

#include "DigitalTwin.h"

namespace SysMLv2::REST{
    DigitalTwin::DigitalTwin(std::string name, std::shared_ptr<Project> owningProject,
    std::shared_ptr<Commit> referencedCommit) : Tag(name,owningProject,referencedCommit) {
        Type = "Twin";
    }

    DigitalTwin::DigitalTwin(const std::string &jsonStringOrName) : Tag(jsonStringOrName) {
        Type = "Twin";
    }
} // SysMLv2::REST