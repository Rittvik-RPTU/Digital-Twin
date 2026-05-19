import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer


import os

# 1. Load Valid Users from ACL

VALID_USERS = {}
try:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    acl_path = os.path.join(base_dir, 'users_acl.json')
    with open(acl_path, 'r') as f:
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
# Testuser's Standard Data
TEST_PROJECT_ID = "990e8400-e29b-41d4-a716-999999999999"
TEST_BRANCH_ID = "660e8400-e29b-41d4-a716-111111111111"
TEST_COMMIT_ID = "770e8400-e29b-41d4-a716-222222222222"

# Admin's IDs
ADMIN_BRANCH_ID = "660e8400-e29b-41d4-a716-333333333333"
ADMIN_COMMIT_ID = "770e8400-e29b-41d4-a716-444444444444"

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
                "@id": "880e8400-e29b-41d4-a716-000000000001",
                "@type": "TextualRepresentation",
                "name": "ClassifiedDroneDef",
                "declaredName": "ClassifiedDroneDef",
                "visibility": "public",
                "body": "part ClassifiedDrone { \n  attribute stealthLevel : Scalar;\n}",
                "language": "SysML"
            }
        ],
        TEST_COMMIT_ID: [
            {
                "@id": "880e8400-e29b-41d4-a716-000000000002",
                "@type": "TextualRepresentation",
                "name": "ElectricCarDef",
                "declaredName": "ElectricCarDef",
                "visibility": "public",
                "body": "part ElectricCar { \n  attribute chargeLevel : Scalar;\n  attribute temperature : Real;\n  attribute speed : Real;\n}",
                "language": "SysML"
            },
            {
                "@id": "880e8400-e29b-41d4-a716-000000000003",
                "@type": "TextualRepresentation",
                "kind": "AttributeUsage",
                "name": "temperature",
                "declaredName": "temperature",
                "visibility": "public",
                "lowerBound": 0.0,
                "upperBound": 120.0,
                "body": "",
                "language": "SysML"
            },
            {
                "@id": "880e8400-e29b-41d4-a716-000000000004",
                "@type": "TextualRepresentation",
                "kind": "AttributeUsage",
                "name": "speed",
                "declaredName": "speed",
                "visibility": "public",
                "lowerBound": 0.0,
                "upperBound": 250.0,
                "body": "",
                "language": "SysML"
            },
            {
                "@id": "880e8400-e29b-41d4-a716-000000000005",
                "@type": "TextualRepresentation",
                "kind": "AttributeUsage",
                "name": "chargeLevel",
                "declaredName": "chargeLevel",
                "visibility": "public",
                "lowerBound": 0.0,
                "upperBound": 100.0,
                "body": "",
                "language": "SysML"
            }
        ]
    }
}

# Which projects belong to which user
USER_PROJECT_OWNERSHIP = {
    "admin": [ADMIN_PROJECT_ID, TEST_PROJECT_ID],
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
    
        if self.path == '/projects' or self.path == '/projects/' or self.path.endswith('/projects'):
            # Extract username from Bearer token (e.g., "Bearer mock-token-admin")
            auth_header = self.headers.get('Authorization', '')
            requesting_user = ""
            if 'mock-token-' in auth_header:
                requesting_user = auth_header.split('mock-token-')[-1]
            
            # Load allowed projects for this user from ACL
            allowed_pids = []
            try:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                acl_path = os.path.join(base_dir, 'users_acl.json')
                with open(acl_path, 'r') as f:
                    acl_data = json.load(f)
                    allowed_pids = acl_data.get('users', {}).get(requesting_user, {}).get('projects', [])
            except: pass

            all_projects = []
            
            # Only add projects from DB if they are in the user's allowed list
            for pid, project_obj in DB["projects"].items():
                if pid in allowed_pids:
                    all_projects.append(project_obj)
            
            # Synthesize other projects from ACL if they belong to this specific user
            for pid in allowed_pids:
                if pid not in DB["projects"]:
                    all_projects.append({
                        "@id": pid,
                        "@type": "Project",
                        "name": f"Dynamic_Project_{pid[:8]}",
                        "description": f"Automatically generated for user {requesting_user}",
                        "defaultBranch": {"@id": f"{pid[:8]}-1111-2222-3333-666666666666", "@type": "Branch", "name": "main"}
                    })
            
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
                    "@id": f"{pid[:8]}-1111-2222-3333-666666666666",
                    "@type": "Branch",
                    "name": "main",
                    "head": {"@id": f"{pid[:8]}-1111-2222-3333-777777777777", "@type": "Commit"}
                }]
            self._send_json(200, branches)
            return

        
        # Route: GET /projects/{projectId}/commits/{commitId}/elements
        
        elements_match = re.search(r'/projects/[^/]+/commits/([^/]+)/elements$', self.path)
        if elements_match:
            cid = elements_match.group(1)
            elements = DB["elements"].get(cid, [])
            if not elements:
                # Synthesize a fake car part with valid hex UUIDs
                elements = [{
                    "@id": f"{cid[:32]}ffff", # Ensure 36 chars if cid is shorter, but cid is 36.
                    "@type": "TextualRepresentation",
                    "declaredName": "DynamicPart",
                    "body": "part DynamicPart { \n  attribute data : Scalar;\n}",
                    "language": "SysML"
                }]
            self._send_json(200, elements)
            return

        
        # Fallback / twins
        
        if self.path.endswith('/twins'):
            # Extract Project ID from path
            pid_match = re.search(r'/projects/([^/]+)/twins$', self.path)
            pid = pid_match.group(1) if pid_match else "unknown"
            
            fake_twin = [{
                "@id": f"{pid[:8]}-1111-2222-3333-444444444444",
                "@type": "Twin",
                "name": "Simulated Live Twin",
                "taggedCommit": {"@id": f"{pid[:8]}-1111-2222-3333-555555555555"},
                "owningProject": {"@id": pid}
            }]
            self._send_json(200, fake_twin)
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
