from app import app
from flask import render_template, request, redirect, url_for, make_response

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            #filename = secure_filename(file.filename)
            file.save("image.jpg")
            triFy("image.jpg",INITIAL_WORKING_WIDTH,INITIAL_THRESHOLD)
            return redirect(url_for('render'))
    return render_template("render.html")
