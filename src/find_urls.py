import re
import requests
import sys
from user_agent import generate_user_agent as ua
import json


class ScanCms:

    def __init__(self):
        if len(sys.argv) == 2:
            self.url = sys.argv[1]
            if self.url.startswith('http://'):
                self.url = self.url.replace('http://', '')
            elif self.url.startswith("https://"):
                self.url = self.url.replace('https://', '')
            elif self.url.startswith("www."):
                self.url = self.url.replace('www.', '')
            else:
                pass

            self.rData = self.check_url_and_request(self.url)
            self.users = []
        else:
            self.rData = None

    def Find_Url(self, r):
        """
        APLICAMOS FILTRO AL CONTENIDO DE LA PAGINA
        PARA OBTENER LAS URLS
        """
        regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
        url = re.findall(regex, r.text)

        """
        BUSCCAMOS PALABRAS EN LAS URLS
        DONDE SE PUEDE ENCONTRAR USUARIOS
        """
        urls = []
        for i in url:
            if "individual" in i[0] or "feed" in i[0] or "author" in i[0] or "dealer" in i[0]:
                if i[0] not in urls:
                    urls.append(i[0])

        """
        RECORREMOS URLS Y SEPARAMOS MEDIANTE /
        TOMAMOS SOLAMENTE EL NOMBRE DEL USUARIO
        """

        for i in urls:

            if "individual" in i:

                auth = re.findall('/individual/(.*)/', i)
                if "/" in auth[0]:
                    author = auth[0].split("/")[0]
                    if author not in self.users:
                        #print("AGREGADO> ", author)
                        self.users.append(author)

            if "author" in i:

                auth = re.findall(
                    '/author/(.*)/', i) or re.findall('/author/(.*)', i)
                print(auth,"------------------------")
                print(len(auth),"*********************")
                if "/" in auth[0]:
                    print("/////",auth)
                    author = auth[0].split("/")[0]

                    if "#" in author:
                        author = author[0].split("#")[0]

                    if author not in self.users:
                        #print("AGREGADO> 1", author)
                        self.users.append(author)
                else:
                    if auth[0] not in self.users:
                        #print("AGREGADO> 2", auth[0])
                        self.users.append(auth[0])

            if "dealer" in i:
                auth = re.findall('/dealer/(.*)/', i)
                if "/" in auth[0]:
                    author = auth[0].split("/")[0]
                    if author not in self.users:
                        #print("AGREGADO> ", author)
                        self.users.append(author)

    def enum_users_author(self):
        for i in range(0, 11):  # 11
            self.page_requests("/?author=" + str(i))

    def enum_users_v2Users(self):
        user = self.page_requests("/wp-json/wp/v2/users/")
        print("----------------------",user)
        print("----------------------",dir(user))
        if user != None:
            print("----------------------",user.status_code)
            if "200" in str(user.status_code):
                users = json.loads(user.text)
                for usr in users:
                    #print("USER:", usr['slug'])
                    if usr['slug'] not in self.users:
                        self.users.append(usr['slug'])

    def check_url_and_request(self, url):

        try:
            r = requests.get(
                'http://'+url, headers={"User-Agent": ua()}, timeout=10)
            if r.status_code == 200:
                return r
            else:
                return None
        except:
            print("Error http")

    def get_theme(self):

        if self.rData != None:
            tema = re.findall('/wp-content/themes/(.*)', self.rData.text)
            theme = []
            for i in tema:
                t = i.split("/")[0].split(",")[0].replace("'", "")

                if t not in theme:
                    theme.append(t)
            print("TEMAS:")
            for i in theme:
                print(i)
            # return theme

    def enumerate_plugins(self):

        if self.rData != None:
            plugins_version = {}
            a = re.findall('/wp-content/plugins/(.*)', self.rData.text)
            for i in a:

                p = i.replace(self.rData.url, '').split("/")[0]
                if p not in plugins_version:
                    plugins_version[p] = 'Unknown'

                    if '?ver=' in i:

                        version = i.split('?ver=')[1].split(
                            "'")[0].replace('"></script>', '')
                        plugins_version[p] = version

            yoast = re.findall(
                'optimized with the Yoast SEO(.*) - http', self.rData.text)
            if len(yoast) == 1:
                plugins_version['Yoast SEO'] = yoast[0]
            #print("PLUGINS: ",plugins_version)
            return plugins_version

    def directory_indexing(self):
        """
         OBTENEMOS PLUGINS Y LOS MANDAMOS POR PARAMETRO
         PAGE.COM/wp-content/plugins/'+(plugin)
        """

        plugins = self.enumerate_plugins()

        if plugins != None:
            print("PLUGINS ", plugins)
            for plugin in plugins.keys():
                data = self.page_requests('/wp-content/plugins/'+plugin)
                if data != None:
                    f = re.findall('Parent Directory', data.text)
                    if len(f) > 0:
                        print("WP-CONTENT/PLUGINS", data.url)

            # /wp-content/uploads/
            up = self.page_requests('/wp-content/uploads/')
            if up != None:
                f = re.findall('Parent Directory', up.text)
                if len(f) > 0:
                    print("WP-CONTENT/UPLOADS", up.url)

            # /wp-includes/
            includes = self.page_requests('/wp-includes/')
            if includes != None:
                f = re.findall('Parent Directory', includes.text)
                if len(f) > 0:
                    print("WP-INCLUDES", includes.url)

    def get_version_cms(self):

        if self.rData != None:
            version = re.findall(
                '<meta name="generator" content="(.*)" />', self.rData.text)

            cms_version = []

            if len(version) > 0:
                extra_data = re.split(
                    '<meta name="generator" content= | />', version[0])

                if len(extra_data) > 1:
                    if extra_data[0].startswith('Powered by'):
                        pass
                    else:
                        cms_version.append(extra_data[0].replace('"', ''))

                    for i in extra_data:

                        if i.startswith('<meta name="generator" content="') and 'Powered by' not in i:

                            cms_version.append(
                                i.replace('<meta name="generator" content="', '').replace('"', ''))

                    for i in cms_version:
                        for x in version:
                            if i not in x:
                                if i.startswith('Powered by'):
                                    pass
                                else:
                                    cms_version.append(i)
                else:
                    for i in version:
                        if i.startswith('Powered by'):
                            pass
                        else:
                            cms_version.append(i)

            for i in cms_version:
                print("CMS VERSION: ", i)

            if 'Server' in self.rData.headers:
                print('Server:', self.rData.headers['Server'])
            if 'X-Powered-By' in self.rData.headers:
                print('Version:', self.rData.headers['X-Powered-By'])

    def page_requests(self, opc):
        #print("iniciando", 'http://'+self.url + opc)
        try:
            r = requests.get('http://'+self.url + opc,
                             headers={"User-Agent": ua()}, timeout=10)
            if r.status_code == 200:

                if "wp-content" in opc or "wp-includes" in opc:
                    return r

                if "/wp-json/wp/v2/users" in opc:
                    return r

                if "/?author=" in opc:
                    self.Find_Url(r)

                if "robots.txt" in opc:
                    return r

                if "wp-config" in opc:
                    return r

            elif r.status_code == 404:
                r = requests.get('https://'+self.url + opc,
                                 headers={"User-Agent": ua()}, timeout=10)

                if r.status_code == 200:

                    if "/?author=" in opc:
                        self.Find_Url(r)

                    if "wp-config" in opc:
                        return r

            elif r.status_code == 405:
                return r

            elif r.status_code == 403:
                return r
            else:
                print(r.status_code, "error!!!!!", opc)

        except requests.exceptions.HTTPError as errh:
            print("Http Error:", errh)
        except requests.exceptions.ConnectionError:
            #print("Error Connecting:",errc)
            return 2
        except requests.exceptions.Timeout as errt:
            print("Timeout Error:", errt)
        except requests.exceptions.RequestException as err:
            print("OOps: Something Else", err)

    def xmlrpc_detect(self):
        xmlrpc = self.page_requests("/xmlrpc.php")
        if xmlrpc != None and xmlrpc != 2:
            print(xmlrpc.url)

    def robots_detect(self):
        robots = self.page_requests("/robots.txt")
        if robots != None:
            print(robots.url)

    def full_path_disclosure(self):
        full_path = self.page_requests("/wp-includes/rss-functions.php")
        if full_path != None:
            fp = full_path.text.replace("<b>", "").replace("</b>", "")
            rex = re.compile("Fatal error:.*? in (.*?) on", re.S)
            path_dis = rex.findall(fp)
            print(path_dis)

    def vulns_plugin_theme(self, Plugin_NaME):
        pass

    def print_data(self):
        print("USUARIOS:")
        for i in self.users:
            print(i)

    def find_backup_files(self):
        backup = ['wp-config.php~', 'wp-config.php.save', '.wp-config.php.bck',
                  'wp-config.php.bck', '.wp-config.php.swp', 'wp-config.php.swp',
                  'wp-config.php.swo', 'wp-config.php_bak', 'wp-config.bak',
                  'wp-config.php.bak', 'wp-config.save', 'wp-config.old',
                  'wp-config.php.old', 'wp-config.php.orig', 'wp-config.orig',
                  'wp-config.php.original', 'wp-config.original', 'wp-config.txt',
                  'wp-config.php.txt', 'wp-config.backup', 'wp-config.php.backup',
                  'wp-config.copy', 'wp-config.php.copy', 'wp-config.tmp',
                  'wp-config.php.tmp', 'wp-config.zip', 'wp-config.php.zip',
                  'wp-config.db', 'wp-config.php.db', 'wp-config.dat',
                  'wp-config.php.dat', 'wp-config.tar.gz', 'wp-config.php.tar.gz',
                  'wp-config.back', 'wp-config.php.back', 'wp-config.test',
                  'wp-config.php.test', "wp-config.php.1", "wp-config.php.2",
                  "wp-config.php.3", "wp-config.php._inc", "wp-config_inc",
                  'wp-config.php.SAVE', '.wp-config.php.BCK',
                  'wp-config.php.BCK', '.wp-config.php.SWP', 'wp-config.php.SWP',
                  'wp-config.php.SWO', 'wp-config.php_BAK', 'wp-config.BAK',
                  'wp-config.php.BAK', 'wp-config.SAVE', 'wp-config.OLD',
                  'wp-config.php.OLD', 'wp-config.php.ORIG', 'wp-config.ORIG',
                  'wp-config.php.ORIGINAL', 'wp-config.ORIGINAL', 'wp-config.TXT',
                  'wp-config.php.TXT', 'wp-config.BACKUP', 'wp-config.php.BACKUP',
                  'wp-config.COPY', 'wp-config.php.COPY', 'wp-config.TMP',
                  'wp-config.php.TMP', 'wp-config.ZIP', 'wp-config.php.ZIP',
                  'wp-config.DB', 'wp-config.php.DB', 'wp-config.DAT',
                  'wp-config.php.DAT', 'wp-config.TAR.GZ', 'wp-config.php.TAR.GZ',
                  'wp-config.BACK', 'wp-config.php.BACK', 'wp-config.TEST',
                  'wp-config.php.TEST', "wp-config.php._INC", "wp-config_INC"
                  ]
        print("Searching backup...")
        for b in backup:

            bk = self.page_requests("/"+b)
            
            if bk != None and bk != 2:
                if 200 == bk.status_code and not "404" in bk.text:
                    print("A wp-config.php backup file has been found in: %s" %
                          (self.url +'/'+ b))
            if bk == 2:
                print("not backup found")
                break


test = ScanCms()
test.enum_users_author()
#test.enum_users_v2Users()
test.print_data()

test.enumerate_plugins()
test.get_theme()
test.get_version_cms()
test.directory_indexing()
test.xmlrpc_detect()
test.robots_detect()
test.full_path_disclosure()
test.find_backup_files()

# buscar /wp-content/debug.log



# TEMAS & PLUGINS
# www.butlerplumbing.com.au
# problema www.absolutelycourier.com




# ROBOTS analizar
# http://elysees-monceau.fr/robots.txt

#ANALIZAR : CORREGIR ERRORES
# doaa.xyz


# problema se queda cargando
# http://www.thehealthylifeline.com


