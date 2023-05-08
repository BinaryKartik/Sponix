from logging import debug
from SongPlayer import create_app
from werkzeug.middleware.profiler import ProfilerMiddleware

app = create_app()
# app.wsgi_app = ProfilerMiddleware(app.wsgi_app, profile_dir="C:\\Users\\Kartik\\OneDrive\\Desktop\\Techno\\sponix-2.0")

if __name__ == '__main__':
    app.run(port=3000, debug=True)

#About 2000 lines of code