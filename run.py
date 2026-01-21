import os
from app import create_app

# Determine environment
env = os.getenv('FLASK_ENV', 'development')
app = create_app(env)

if __name__ == '__main__':
    port = app.config['PORT']
    debug = app.config['DEBUG']
    
    print(f"Server running on port {port}")
    print(f"Environment: {env}")
    print(f"Debug mode: {debug}")
    print(f"API Documentation available at http://localhost:{port}/api-docs")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
