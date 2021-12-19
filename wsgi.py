from gitfitti import init_app
from waitress import serve

app = init_app()
app.app_context().push()

from gitfitti import celery

if __name__ == "__main__":
    serve(app, port=5000)
    # app.run()
