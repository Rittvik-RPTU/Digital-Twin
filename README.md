[toc]

# DigitalTwinKi4Boarnet

## Structure


## Getting started
### Conan
What is conan? Conan is a C++ package manager allowing us to change packages and also allows to install multible versions of one Package.
 1. Install conan. See therefore conan.io
 2. Create build folder within your source folder ```mkdir build && cd build```
 3. Install packages ```conan install .. -s build_type=Debug```
 4. Generate all build files from conan with your first build. ```conan build .. -s build_type=Debug```



# Digital Twin Models for Testing

In this project are also multible SysMLv2 Models for the creation of the Digital Twin. The Models are stored in the following Files:

 - [Original Testing Project](Markdownfiles/DTTester4Project.md)
 - [Functional DT Project](Markdownfiles/DT4Airbag.md)
 - [AI Thread Protected DT](Markdownfiles/SecuredDT.md)



## Security and Access Control

The Digital Twin Server (`DTServer`) now implements credential-based authentication and project-level isolation.

### 1. Broker Configuration (`users_acl.json`)
The broker uses a local Access Control List (ACL) file named `users_acl.json` to map authenticated users to their permitted Project UUIDs. 

To grant a user access to a project:
1. Open `users_acl.json` in the root directory.
2. Add the user's SysML v2 username.
3. List the Project UUIDs they are authorized to access.

### 2. Dynamic Reloading
The broker supports **dynamic ACL updates**. You can modify `users_acl.json` while the broker is running; the new permissions will be applied automatically the next time a user connects. There is no need to restart the server.

To test the security features, you can use the mock server provided in the `tests/` directory:
```bash
python3 tests/mock_agila_server.py
```

### 4. Automated Security Test Suite
You can run the comprehensive test suite to verify the security implementation:
```bash
python3 tests/test_acl.py
```
This script automatically verifies three critical scenarios:
*   **Multi-Tenant Isolation:** Proves a standard user is blocked and kicked if they attempt to access Admin projects.
*   **Dynamic Synchronization:** Proves that new users added to `users_acl.json` are instantly recognized by both the Broker and the Mock Server.
*   **Authorized Access:** Proves that legitimate users (like Admins) have full access to their sensitive projects.
