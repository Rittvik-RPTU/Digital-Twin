import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer


# 1. Load Valid Users from ACL

VALID_USERS = {}
try:
    with open('users_acl.json', 'r') as f:
        acl_data = json.load(f)
        for username in acl_data.get('users', {}):
            if username == "admin":
                VALID_USERS["admin"] = "admin"
            elif username == "testuser":
                VALID_USERS["testuser"] = "testpass"
            else:
                # For any other user, the password is 'pass'
                VALID_USERS[username] = "pass"
except Exception as e:
    print(f"Warning: Could not load users from users_acl.json: {e}")
    VALID_USERS = {"admin": "admin", "testuser": "testpass"}


# 2. Mock Data Database (Proper Hierarchy)


# Admin's Confidential Data
ADMIN_PROJECT_ID = "550e8400-e29b-41d4-a716-446655440000"
ADMIN_BRANCH_ID = "660e8400-e29b-41d4-a716-adminbranch1"
ADMIN_COMMIT_ID = "770e8400-e29b-41d4-a716-admincommit1"

# Testuser's Standard Data
TEST_PROJECT_ID = "990e8400-e29b-41d4-a716-999999999999"
TEST_BRANCH_ID = "660e8400-e29b-41d4-a716-testbranch01"
TEST_COMMIT_ID = "770e8400-e29b-41d4-a716-testcommit01"

# Database representing the server state
DB = {
    "projects": {
        ADMIN_PROJECT_ID: {
            "@id": ADMIN_PROJECT_ID,
            "@type": "Project",
            "name": "Admin_Confidential_Project",
            "description": "Sensitive admin-only data",
            "defaultBranch": {"@id": ADMIN_BRANCH_ID, "@type": "Branch", "name": "main"}
        },
        TEST_PROJECT_ID: {
            "@id": TEST_PROJECT_ID,
            "@type": "Project",
            "name": "Standard_User_Project",
            "description": "Public research data",
            "defaultBranch": {"@id": TEST_BRANCH_ID, "@type": "Branch", "name": "main"}
        }
    },
    "branches": {
        ADMIN_PROJECT_ID: [
            {
                "@id": ADMIN_BRANCH_ID,
                "@type": "Branch",
                "name": "main",
                "head": {"@id": ADMIN_COMMIT_ID, "@type": "Commit"}
            }
        ],
        TEST_PROJECT_ID: [
            {
                "@id": TEST_BRANCH_ID,
                "@type": "Branch",
                "name": "main",
                "head": {"@id": TEST_COMMIT_ID, "@type": "Commit"}
            }
        ]
    },
    "commits": {
        ADMIN_PROJECT_ID: [
            {"@id": ADMIN_COMMIT_ID, "@type": "Commit", "message": "Initial admin commit"}
        ],
        TEST_PROJECT_ID: [
            {"@id": TEST_COMMIT_ID, "@type": "Commit", "message": "Initial testuser commit"}
        ]
    },
    "elements": {
        ADMIN_COMMIT_ID: [
            {
                "@id": "880e8400-e29b-41d4-a716-adminelem001",
                "@type": "TextualRepresentation",
                "name": "ClassifiedDroneDef",
                "body": "part ClassifiedDrone { \n  attribute stealthLevel : Scalar;\n}",
                "language": "SysML"
            }
        ],
        TEST_COMMIT_ID: [
            {
                "@id": "880e8400-e29b-41d4-a716-testelem0001",
                "@type": "TextualRepresentation",
                "name": "ElectricCarDef",
                "body": "part ElectricCar { \n  attribute chargeLevel : Scalar;\n}",
                "language": "SysML"
            }
        ]
    }
}

# Which projects belong to which user
USER_PROJECT_OWNERSHIP = {
    "admin": [ADMIN_PROJECT_ID],
    "testuser": [TEST_PROJECT_ID]
}


# 3. Request Handler

class MockSysMLHandler(BaseHTTPRequestHandler):
    
    def _get_user_from_token(self):
        auth_header = self.headers.get('Authorization', '')
        if 'mock-token-' in auth_header:
            return auth_header.split('mock-token-')[1]
        return None

    def _send_json(self, status, data):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        user = self._get_user_from_token()

        if self.path == '/version':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'7')
            return

        
        # Route: GET /projects
    
        if self.path == '/projects' or self.path == '/projects/':
            # Collect projects from hardcoded DB + synthesized projects from ACL
            all_projects = list(DB["projects"].values())
            
            # Synthesize projects for users in ACL not in hardcoded DB
            try:
                with open('users_acl.json', 'r') as f:
                    acl = json.load(f)
                    for u, data in acl.get('users', {}).items():
                        for pid in data.get('projects', []):
                            if pid not in DB["projects"]:
                                # Add a fake project object for this ACL project
                                all_projects.append({
                                    "@id": pid,
                                    "@type": "Project",
                                    "name": f"Dynamic_Project_{pid[:8]}",
                                    "description": f"Automatically generated for user {u}",
                                    "defaultBranch": {"@id": f"branch-{pid[:8]}", "@type": "Branch", "name": "main"}
                                })
            except: pass
            
            self._send_json(200, all_projects)
            return

        
        # Route: GET /projects/{projectId}/branches
        
        branches_match = re.search(r'/projects/([^/]+)/branches$', self.path)
        if branches_match:
            pid = branches_match.group(1)
            branches = DB["branches"].get(pid, [])
            if not branches:
                # Synthesize a branch if not in DB but looks like an ACL project
                branches = [{
                    "@id": f"branch-{pid[:8]}",
                    "@type": "Branch",
                    "name": "main",
                    "head": {"@id": f"commit-{pid[:8]}", "@type": "Commit"}
                }]
            self._send_json(200, branches)
            return

        
        # Route: GET /projects/{projectId}/commits/{commitId}/elements
        
        elements_match = re.search(r'/projects/[^/]+/commits/([^/]+)/elements$', self.path)
        if elements_match:
            cid = elements_match.group(1)
            elements = DB["elements"].get(cid, [])
            if not elements:
                # Synthesize a fake car part
                elements = [{
                    "@id": f"elem-{cid[:8]}",
                    "@type": "TextualRepresentation",
                    "name": "DynamicPart",
                    "body": "part DynamicPart { \n  attribute data : Scalar;\n}",
                    "language": "SysML"
                }]
            self._send_json(200, elements)
            return

        
        # Fallback / twins
        
        if self.path.endswith('/twins'):
            self._send_json(200, [])
            return

        # If route not found
        self._send_json(404, {"error": "Endpoint not mocked"})

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode() if content_length > 0 else ''

        
        # Route: POST /login
        
        if self.path == '/login' or self.path == '/agila-server/users/login':
            try:
                creds = json.loads(body) if body else {}
                username = creds.get('username', '')
                password = creds.get('password', '')
            except json.JSONDecodeError:
                username, password = '', ''

            if username in VALID_USERS and VALID_USERS[username] == password:
                self._send_json(200, {"barrierString": f"mock-token-{username}"})
            else:
                self._send_json(401, {"error": "Invalid credentials"})
            return

        # Fallback
        self._send_json(200, {})


def run(server_class=ThreadingHTTPServer, handler_class=MockSysMLHandler, port=8088):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting simulated SysML v2 mock server on port {port}...")
    print(f"  Valid users: {list(VALID_USERS.keys())}")
    print(f"  Mock projects: {list(DB['projects'].keys())}")
    httpd.serve_forever()

if __name__ == '__main__':
    run()
