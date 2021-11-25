from gitfitti import init_app
from waitress import serve

app = init_app()

if __name__ == "__main__":
    serve(app)