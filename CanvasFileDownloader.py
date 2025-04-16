#Program to download all of your canvas submission files
import requests
import os
from datetime import datetime
import configparser
import shutil
#parse config
parser = configparser.ConfigParser()
parser.read('config.ini')
token = parser.get('USER','TOKEN')
domain = parser.get('USER','DOMAIN')

params = {
    'include[]': [
        'user',
        'usage_rights',
        'enhanced_preview_url',
        'context_asset_string',
    ],
    'order': '',
    'sort': '',
    'page': '1',
    'per_page': 100,
    }


#class to be put in a list
class EnrolledClass:
    def __init__(self,id,name,semester,createdate,folderurl):
        self.id = id
        self.name = name
        self.semester = semester
        self.createdate = createdate
        self.folderurl = folderurl
    def __str__(self):
        return f'{self.id} , {self.name} , {self.semester} , {self.createdate} , {self.folderurl}'

    def GetSemester(self):
        return self.semester
    
    def GetClass(self):
        return self.name
    
    def GetCreateDate(self):
        return self.createdate
    
    def GetID(self):
        return self.id
    
    def GetFiles(self):
        return self.folderurl


#function that uses your domain and token to get the id of your submissions folder.
#returns the number of id and the amount of classes you have
def getrootfolder() -> tuple[str,str]:

    #the first part is to get the users id
    url = f'https://webcourses.{domain}/api/v1/users/self?access_token={token}'
   
    response = requests.get(url)
    userid = response.json()['id']

    #gets the id of the submissions folder
    url = f'https://webcourses.{domain}/api/v1/users/{userid}/folders/by_path?access_token={token}'
    response = requests.get(url)
    rootfolderid = response.json()[0]['id']

    #from the root folder we can get the submission folder id
    url = f'https://webcourses.{domain}/api/v1/folders/{rootfolderid}/folders?access_token={token}'
    response = requests.get(url)
    #Data for your submissions root folder
    folderdata = response.json()

    for folder in folderdata:
        if folder['name'] == 'Submissions':
            submissionid = folder['id']

    return submissionid

#uses the canvas api to get the list of classes
def getclasses(folderid) -> list:

    #The list of submissions for each user
    submissionfolder = f'https://webcourses.{domain}/api/v1/folders/{folderid}/folders?access_token={token}'
    response = requests.get(
        url=submissionfolder,
        params=params
    )
    #get the json of submissions
    submissionJSON = response.json()

    response = requests.get(
        url=f'https://webcourses.{domain}/api/v1/courses?access_token={token}',
        params=params
    )
    #print(response.url)
    classjson = response.json()
    classlist = []



    for userclass in classjson:
        #Some classes dont have a name field, so we will skip those
        name = userclass.get('name')
        #if userclass['access_restricted_by_date']
        if name is not None:
            classlist.append(
            EnrolledClass(
                userclass['id'],                            #class id
                userclass['course_code'],                          #class name
                userclass['enrollment_term_id'],           #class semester
                userclass['created_at'],                   #when the class was created at
                #we need to add the folder url if it is in there
                getfolderurl(submissionJSON,userclass['course_code'])
            )
            )


    #now we need to assign each semester to the class

    response = requests.get(
        url=f'https://webcourses.{domain}/api/v1/courses?access_token={token}',
        params=params
    )

    return classlist


def getfolderurl(submissionJSON,classname):
    for item in submissionJSON:
        if item['name'] == classname:
            return item['files_url']
        

    return 'nofiles'


#this function creates a dir structure of semester -> class -> assignments
#Used to create the folders and download all of the files.
def downloaddata(classlist):

    semesterlist = []

    for c in classlist:
        #create the list of senesters

        if c.GetSemester() not in semesterlist:
            semesterlist.append(c.GetSemester())
            #create the file directory
            #Check if the directory already exists
            if os.path.exists(c.GetSemester()):
                print(f'{c.GetSemester()} already exists. Overwriting.')
                shutil.rmtree(c.GetSemester())


            try:
                os.mkdir(f'sem{c.GetSemester()}')
                print(f'Succeeded to create semester directory - {c.GetSemester()}')
            except :
                print(f'Failed to create semester directory - {c.GetSemester()}')

        #once the files are creeated we create the class folder in the semester directory
        classpath = f'sem{c.GetSemester()}/{c.GetClass()}'

        if os.path.exists(classpath):
                print(f'{c.GetClass()} already exists. Overwriting.')
                shutil.rmtree(classpath)
        try:
            os.mkdir(classpath)
            print(f'Succeeded to create class directory - {c.GetClass()}')
            dt = datetime.strptime(c.GetCreateDate(),'%Y-%m-%dT%H:%M:%SZ')
            createdtime = int(dt.timestamp())
            os.utime(classpath,(createdtime,createdtime))
            os.mkdir(f'{classpath}/lectures')
            os.mkdir(f'{classpath}/assignments')
        #
        except:
            print(f'Failed to create class directory - {c.GetClass()}')

        #WIP
        print(f'Downloading lectures for {c.GetClass()}')
        downloadlectures(classparams=params,classitem=c)
        print(f'Downloading assignments for {c.GetClass()}')
        downloadassignments(classparams=params,classitem=c)

       
#WIP
#This needs some work. We need to download the entire file directory and any subfolders.
#Some pages have files and some had modules. 
def downloadlectures(classparams,classitem):
 
    #Get the json of each file list

    #Try a files download first
    response = requests.get(url = f'https://webcourses.{domain}/api/v1/courses/{classitem.GetID()}/files?access_token={token}',params=classparams)
    #modules try
    filedata = response.json()

    if 'errors' in filedata and filedata['errors']:
        print('Cannot download from files. Will try modules WIP!!!!!!')
        return
    for file in filedata:
        response = requests.get(url = f'{file['url']}',params=classparams)
        lecturepath=f'sem{classitem.GetSemester()}/{classitem.GetClass()}/lectures/{file['filename']}'
     
        if response.status_code == 200:
            try:
                with open(lecturepath,'wb') as assignmentfile:
                        assignmentfile.write(response.content)
                        print(f'Download succesful - {file['filename']}')

                        #set the times for the time
                        dt = datetime.strptime(file['created_at'],'%Y-%m-%dT%H:%M:%SZ')
                        createdtime = int(dt.timestamp())

                        dt = datetime.strptime(file['updated_at'],'%Y-%m-%dT%H:%M:%SZ')
                        modtime = int(dt.timestamp())
                        
                        #issue. unix systems do not allow modification of the created time. So we need to update this
                        #set the accesstime and mod time to the canvas date

                        os.utime(lecturepath, (modtime, createdtime))

            except:
                    print(f'Download failed - {file['filename']}.')

        else:
            print(f'Download failed - {file['filename']}. Web Error.')
         
def downloadassignments(classparams,classitem):
        
        if classitem.GetFiles() != 'nofiles':
        
            #request the class json page
            response = requests.get(url = f'{classitem.GetFiles()}?access_token={token}',
                                    params=classparams
                                    )
            
            #this is all of the class information in a json. We will parse this and download each of the files from here.
            classjson = response.json()
            #for each assignment in a class
            for assignment in classjson:
        
                #diwnload the assignment 
                #response = requests.get(url = f'{assignment['url']}?access_token={token}')
                response = requests.get(url = f'{assignment['url']}')

                assignmentpath = f'sem{classitem.GetSemester()}/{classitem.GetClass()}/assignments/{assignment['filename']}'
                #Assignment downloader
                if response.status_code == 200:
                    try:
                        with open(assignmentpath,'wb') as assignmentfile:
                            assignmentfile.write(response.content)
                            print(f'Download succesful - {assignment['filename']}')

                            #set the times for the time
                            dt = datetime.strptime(assignment['created_at'],'%Y-%m-%dT%H:%M:%SZ')
                            createdtime = int(dt.timestamp())

                            dt = datetime.strptime(assignment['updated_at'],'%Y-%m-%dT%H:%M:%SZ')
                            modtime = int(dt.timestamp())
                            
                            #issue. unix systems do not allow modification of the created time. So we need to update this
                            #set the accesstime and mod time to the canvas date
                            os.utime(assignmentpath, (modtime, createdtime))
                    except:
                        print(f'Download failed - {assignment['filename']}.')
                else:
                    print(f'Download failed - {assignment['filename']}. Web Error.')

            else:
                print(f'No downloadable assignments for{classitem.GetClass()}')
                return     
            
#main function
def main():
    print('Starting Canvas Downloader\n')
    folderid = getrootfolder()
    classlist = getclasses(folderid)
    downloaddata(classlist=classlist)
    
   
if __name__=="__main__":
    main()
