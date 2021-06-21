from jinja2 import Environment, FileSystemLoader
import os, argparse, shutil

API_URL_ENV_VARNAME = "DATACATALOG_API_URL"
API_URL_DEFAULT_VALUE = "http://localhost:8000/"

def render_template_to_site(api_url=API_URL_DEFAULT_VALUE):
    ## copy javascript files to site folder
    src_files = os.listdir('frontend/js')
    dest = 'site/js'
    os.makedirs(dest, exist_ok=True)

    for file_name in src_files:
        full_name = os.path.join('frontend/js', file_name)
        if os.path.isfile(full_name):
            shutil.copy(full_name, dest)
    
    ## copy css files to site folder
    src_files = os.listdir('frontend/css')
    dest = 'site/css'
    os.makedirs(dest, exist_ok=True)

    for file_name in src_files:
        full_name = os.path.join('frontend/css', file_name)
        if os.path.isfile(full_name):
            shutil.copy(full_name, dest)

    ## replace {{API_URL}} tag with actual api url from env
    apicalls_file_path = 'site/js/apicalls.js'
    api_tag = '{{API_URL}}'
    with open(apicalls_file_path, 'r') as file:
        filedata = file.read()
    filedata = filedata.replace(api_tag, api_url)
    with open(apicalls_file_path, 'w') as file:
        file.write(filedata)


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
    # priority for setting the API URL from most to least important: commandline argument >>> environment variable >>> default value

    # if env variable is set, get api url from it, else use default
    api_url = os.getenv(API_URL_ENV_VARNAME, API_URL_DEFAULT_VALUE)
    # if argument is there, set api url
    parser = argparse.ArgumentParser("createStatic.py", description="Generates the static files for the web frontend to the site/ folder.")
    parser.add_argument("-u", "--api-url", help="The url for the backend API. This must include protocol (usually http or https). Defaults to {} or the environment variable {} (if set).".format(API_URL_DEFAULT_VALUE, API_URL_ENV_VARNAME))
    args = parser.parse_args()
    if args.api_url:
        api_url = args.api_url

    print(api_url)

    render_template_to_site(api_url)