import json
import re
from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer


import os

# 1. Define Bounds Model for Payload Validation

BOUNDS_MODELS = {
    # Test/Standard User Project - Electric Car Attributes
    "990e8400-e29b-41d4-a716-999999999999": {
        "temperature": {"min": 0.0, "max": 120.0, "unit": "°C"},
        "speed": {"min": 0.0, "max": 250.0, "unit": "km/h"},
        "chargeLevel": {"min": 0.0, "max": 100.0, "unit": "%"}
    },
    # Admin Confidential Project - Drone Attributes
    "550e8400-e29b-41d4-a716-446655440000": {
        "stealthLevel": {"min": 0.0, "max": 10.0, "unit": "level"},
        "altitude": {"min": 0.0, "max": 50000.0, "unit": "meters"}
    }
}

# 2. Load Valid Users from ACL

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
            elif username == "superadmin":
                VALID_USERS["superadmin"] = "superadmin"
            else:
                # For any other user, the password is 'pass'
                VALID_USERS[username] = "pass"
except Exception as e:
    print(f"Warning: Could not load users from users_acl.json: {e}")
    VALID_USERS = {"admin": "admin", "testuser": "testpass"}


# 3. Mock Data Database (Proper Hierarchy)


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

# 4. Request Handler

class MockSysMLHandler(BaseHTTPRequestHandler):

    def _generate_attribute_usage_elements(self, project_id):
        """Generate AttributeUsage elements from BOUNDS_MODELS.

        Each attribute becomes a TextualRepresentation element with lowerBound/upperBound.
        This allows AuthenticationService to fetch bounds dynamically from the mock server.
        """
        elements = []

        if project_id not in BOUNDS_MODELS:
            return elements  # No bounds defined for this project

        element_id_base = project_id[:8]  # Use first 8 chars of project UUID
        counter = 3  # Start from 3 to avoid conflicts with static elements

        for attr_name, bounds_info in BOUNDS_MODELS[project_id].items():
            element = {
                "@id": f"{element_id_base}400-e29b-41d4-a716-00000000000{counter}",
                "@type": "TextualRepresentation",
                "kind": "AttributeUsage",
                "name": attr_name,
                "declaredName": attr_name,
                "visibility": "public",
                "lowerBound": bounds_info["min"],
                "upperBound": bounds_info["max"],
                "unit": bounds_info.get("unit", ""),
                "body": f"attribute {attr_name} : Real;",
                "language": "SysML"
            }
            elements.append(element)
            counter += 1

        return elements

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
            
            # Gather all projects globally across all users in the ACL to simulate the standard API gap
            global_pids = set(DB["projects"].keys())
            try:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                acl_path = os.path.join(base_dir, 'users_acl.json')
                with open(acl_path, 'r') as f:
                    acl_data = json.load(f)
                    for u_entry in acl_data.get('users', {}).values():
                        for pid in u_entry.get('projects', []):
                            global_pids.add(pid)
            except: pass

            all_projects = []
            
            # Add database projects
            for pid, project_obj in DB["projects"].items():
                all_projects.append(project_obj)
            
            # Add other projects from ACL (simulating the global leaky view)
            for pid in global_pids:
                if pid == "*":
                    continue
                if pid not in DB["projects"]:
                    all_projects.append({
                        "@id": pid,
                        "@type": "Project",
                        "name": f"Global_Project_{pid[:8]}",
                        "description": "Global project leaked by standard SysML v2 REST endpoint",
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

        elements_match = re.search(r'/projects/([^/]+)/commits/([^/]+)/elements$', self.path)
        if elements_match:
            project_id = elements_match.group(1)
            commit_id = elements_match.group(2)

            # First, check if elements are in DB (static test data)
            elements = DB["elements"].get(commit_id, [])

            # If not in DB, generate bounds from BOUNDS_MODELS
            if not elements:
                elements = self._generate_attribute_usage_elements(project_id)

            # If still no elements, synthesize a generic part
            if not elements:
                elements = [{
                    "@id": f"{commit_id[:32]}ffff",
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
