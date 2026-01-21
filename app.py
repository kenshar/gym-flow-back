from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 

members_data = [
    { "id": 1, "name": "Branice Nashilu", "status": "Active", "plan": "Gold" },
    { "id": 2, "name": "John Doe", "status": "Expired", "plan": "Silver" },
    { "id": 3, "name": "Jane Smith", "status": "Active", "plan": "Platinum" },
    { "id": 4, "name": "Michael Kamau", "status": "Active", "plan": "Silver" },
    { "id": 5, "name": "Sarah Ochieng", "status": "Expired", "plan": "Gold" },
    { "id": 6, "name": "David Njoroge", "status": "Active", "plan": "Platinum" },
    { "id": 7, "name": "Emily Wanjiku", "status": "Active", "plan": "Gold" },
    { "id": 8, "name": "Brian Kiprop", "status": "Expired", "plan": "Silver" },
    { "id": 9, "name": "Alice Mwikali", "status": "Active", "plan": "Silver" },
    { "id": 10, "name": "Kevin Otieno", "status": "Active", "plan": "Platinum" },
    { "id": 11, "name": "Grace Nyambura", "status": "Expired", "plan": "Gold" },
    { "id": 12, "name": "Samuel Mwangi", "status": "Active", "plan": "Gold" },
    { "id": 13, "name": "Linda Achieng", "status": "Active", "plan": "Silver" }
]

@app.route('/members', methods=['GET'])
def get_members():
    return jsonify(members_data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
