from replit import db

for key in db.keys():
    if db[key]['join_time'] is not None:
        db[key]['join_time'] = None