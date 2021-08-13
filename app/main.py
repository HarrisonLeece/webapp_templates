import os
from flask import Flask, session, redirect, url_for, render_template, request, flash
from flask_sqlalchemy import SQLAlchemy
import sys
import re
import Levenshtein as lsh

app = Flask(__name__, template_folder='templates')
app.config.update(TESTING=True, TEMPLATES_AUTO_RELOAD=True)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL') or 'sqlite:///users.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = '1!df56dn;'

db = SQLAlchemy(app)


class chat_line(db.Model):
    _id = db.Column('id', db.Integer, primary_key=True)
    user_name = db.Column(db.String(100))
    comment = db.Column(db.String(550))

    def __init__(self, user_name, comment):
        self.user_name = user_name
        self.comment = comment


def clear_data(session):
    meta = db.metadata
    for table in reversed(meta.sorted_tables):
        # print('Clear table %s' % table)
        session.execute(table.delete())
    session.commit()


@app.route("/", methods=['GET', 'POST'])
def home():
    return redirect('/app')


@app.route("/app/", methods=["GET", "POST"])
def webapp():
    try:
        clear_data(db.session)
    except:
        pass
    if request.method == "POST":
        posted_url = request.form["url"]
        split_url_list = re.split("/", posted_url)
        vid_id = [x for x in split_url_list if re.match('^[0-9]*$',x)][-1]
        posted_action = request.form["action_type"]
        try:
            import twitch
            helix = twitch.Helix('s57g6gzad97sk5f89scejz2lwal6gn',
                                 'i0ywhsktt3y3fmavyufmp8d5jnb5o5', use_cache=True)

            for video, comments in helix.videos([vid_id]).comments:
                for comment in comments:
                    n = 9999
                    user = comment.commenter.display_name
                    text = comment.message.body
                    # print(user + text)
                    this_line = chat_line(user, text)
                    # print(this_line)
                    db.session.add(this_line)
                    # print('added')

                    # print('committed')
                    if n == 10000:
                        n = 0
                        # print('loading comments...')
                    n += 1
                db.session.commit()
            # desired action of this page
            #if request.form["action_type"] == 1:
                #pass
            #else:
                #return redirect('/chat_text')
            return redirect('/chat_text')
        except:
            e = sys.exc_info()[0]
            return render_template('app_error.html', title="Twitch Scraper", url=vid_id, action=posted_action, error=e)
    else:
        return render_template('app.html', title="Twitch Scraper")


@app.route("/chat_text/", methods=["GET", "POST"])
def show_chat_text():
    try:
        comment_list = []
        for line in chat_line.query.all():
            comment_list.append(line.user_name + ': ' + line.comment)
        num_comments = len(comment_list)

        if request.method == "GET":
            return render_template('text_page.html', data=comment_list, num_coms=num_comments, search_standin = 0)
        else:
            x = request.form['search_form_input']
            fuzz = request.form['fuzz_range']
            num_terms = 0
            for line in comment_list:
                word_list = line.split()
                del word_list[0]
                for word in word_list:
                    if (lsh.distance(word, x) <= int(fuzz)):
                        num_terms += 1
            return render_template('text_page.html', data=comment_list, num_coms=num_comments, search_standin = num_terms)
    except:
        e = sys.exc_info()[0]
        print(e)
        clear_data(db.session)
        return redirect('/app')



@app.route("/help/", methods=['GET'])
def help():
    return render_template('help.html', title="Help")


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
