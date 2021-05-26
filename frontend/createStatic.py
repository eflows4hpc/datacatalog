from jinja2 import Environment, FileSystemLoader
import os
import shutil

def main():
    ## copy javascript files to site folder
    src_files = os.listdir('frontend/js')
    dest = 'site/js'
    os.makedirs(dest, exist_ok=True)
    #os.mkdir(dest)

    for file_name in src_files:
        full_name = os.path.join('frontend/js', file_name)
        if os.path.isfile(full_name):
            shutil.copy(full_name, dest)

    ## render templates to site folder
    file_loader = FileSystemLoader('frontend/templates')
    env = Environment(loader=file_loader)

    files = {
        'index' : 'index_content.html.jinja',
        'storage' : 'storage_content.html.jinja',
        'impressum' : 'impressum_content.html.jinja',
        'login' : 'login_content.html.jinja'
    }

    templates = {}

    for file in files.keys():
        templates[file] = env.get_template(files[file])

    html = {}


    html['index'] = templates['index'].render(home=True)
    html['storage'] = templates['storage'].render(storage=True)
    html['impressum'] = templates['impressum'].render(impressum=True)
    html['login'] = templates['login'].render(login=True)

    for file in files.keys():
        with open('site/'+file+'.html', 'w') as f:
            f.write(html[file])

if __name__ == "__main__":
    main()