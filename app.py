import os
from flask import Flask, render_template, request, send_file, after_this_request
import yt_dlp

app = Flask(__name__)

# Temporary folder to safely hold downloads before serving them
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/')
def index():
    # Flask automatically finds this inside the templates folder!
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    url = request.form.get('url')
    format_type = request.form.get('format')
    
    if not url:
        return "Error: URL is empty", 400

    # Restricts file names so long social media titles don't crash Android/Linux
    out_template = os.path.join(DOWNLOAD_FOLDER, '%(title).30s_[%(id)s].%(ext)s')
    
    ydl_opts = {
        'outtmpl': out_template,
        'quiet': True,
    }

    if format_type == 'audio':
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '0',
        }]
    else:
        ydl_opts['format'] = 'bestvideo+bestaudio/best'
        ydl_opts['merge_output_format'] = 'mp4'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if format_type == 'audio':
                filename = os.path.splitext(filename)[0] + '.mp3'

        # This cleans up the server automatically after your friend gets their download
        @after_this_request
        def cleanup(response):
            try:
                if os.path.exists(filename):
                    os.remove(filename)
            except Exception as e:
                print(f"Cleanup error: {e}")
            return response

        return send_file(filename, as_attachment=True)

    except Exception as e:
        return f"Download failed: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)
