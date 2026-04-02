//
// Created by Moritz Herzog on 22.07.25.
//

#ifndef DIGITALTWIN_H
#define DIGITALTWIN_H

#include <sysmlv2/rest/entities/Tag.h>
#include <boost/uuid/uuid.hpp>

#include "../cpp_backend_communication_global.h"

namespace SysMLv2::REST {

    /**
        * This class Represents a Digital Twin Object that is sent to the Digital Twin Client and Server.
        * @class DigitalTwin
        * @author Moritz Herzog <herzogm@rptu.de>
        * @version 1.0
        * @see Record
        */
    class CPSBACKENDCOMMUNICATION_EXPORT DigitalTwin : public SysMLv2::REST::Tag {
    public:
        explicit DigitalTwin(std::string name, std::shared_ptr<SysMLv2::REST::Project> owningProject, std::shared_ptr<SysMLv2::REST::Commit> referencedCommit);
        explicit DigitalTwin(const std::string &jsonStringOrName);
        virtual ~DigitalTwin() = default;

    };

} // SysMLv2::REST

#endif //DIGITALTWIN_H
