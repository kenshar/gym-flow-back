from app import create_app

app = create_app('development')

if __name__ == '__main__':
    print(f"Server running on port {app.config['PORT']}")
    print(f"API Documentation available at http://localhost:{app.config['PORT']}/api-docs")
    app.run(host='0.0.0.0', port=app.config['PORT'], debug=True)
