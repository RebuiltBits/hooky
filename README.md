# Hooky

A simple, flexible and fast [web hook](http://en.wikipedia.org/wiki/Webhook) translation service written in Python.

The goal of Hooky is to provide a simple customizable web service that can translate incoming web hooks from various services into other outbound RPC calls (web hooks, emails, etc). Using a simple set of configuration files, you define how to translate content posted to the Hooky service into a format that another remote service will accept.

*Wait … Why? What?*

Web hooks are great ways for different services to share information with each other. The problem though is that in order for two services to communicate, the *sender* and *receiver* must speak the same language. This leads to a whole lot of work keeping up with various services and their inbound web hook formats. Just look at the [Github Service Hooks](https://github.com/github/github-services/tree/master/docs) that they've built to keep up with various external services.

This little app provides a translation service where you can define how to translate a web hook from one format to another. For example, you can translate a Github generic web hook into a custom call out to a service that they do not support, like [Librato](http://librato.com)

## Installation

To install, run

    python setup.py install

or

    pip install hooky
    
## Running It

Running Hooky is simple... it acts as a basic webserver that listens to the supplied port and responds to queries. The simplest way to run it is:

    MacBook-Pro:hooky $ hooky --help
    Usage: hooky <options>
    
    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -C CONFIG_MODULE, --configModule=CONFIG_MODULE
                            Override the default configuration provider (def:
                            hooky.config.file.FileConfig)
      -c CONFIG_FILE, --configFile=CONFIG_FILE
                            Override the default file (def: config.ini)
      -p PORT, --port=PORT  Port to listen to (def: 8080)
      -l LEVEL, --level=LEVEL
                            Set logging level (INFO|WARN|DEBUG|ERROR)
      -s SYSLOG, --syslog=SYSLOG
                            Log to syslog. Supply facility name. (ie "local0")
    MacBook-Pro:hooky $
    
Running it in verbose mode with console logging:

    MacBook-Pro:hooky $ hooky -l debug -c config.ini 
    [5931] [root] [main]: (DEBUG) Building config object...
    [5931] [hooky.utils] [strToClass]: (DEBUG) Translating "hooky.config.file.FileConfig" into a Module and Class...
    [5931] [hooky.utils] [strToClass]: (DEBUG) Module: hooky.config.file, Class: FileConfig
    [5931] [hooky.utils] [strToClass]: (DEBUG) Class Reference: <class 'hooky.config.file.FileConfig'>
    [5931] [hooky.config.file] [__init__]: (INFO) Instantiating FileConfig with config file: config.ini

Or, if you'd rather have logs sent to syslog:

    Matts-MacBook-Pro-2:hooky diranged$ hooky -l debug -c config.ini -s local0
    ...


## Configuration

Hooky is designed to support different configuration methods and systems as
people build them. By default it ships with a file-based configuration module.
In the future additional modules may allow it to be configured via a database,
or Zookeeper, or S3… Simply subclass the *hooky.config.base.BaseConfig* class
and build your own module if you like!

### hooky.config.file.FileConfig
*Default Configuration Module*

The FileConfig class reads in a single configuration file (passed via the
command line as an option). This configuration file has one *[general]* section,
and then individual sections defining web hooks and translators.

Here's an example file:

    [general]
    templates: templates
    
    [githubToPost]
    type: hook
    translators: GithubToHttpbinPost
    
    [GithubToHttpbinPost]
    type: translator
    translator: hooky.translators.web.PostTranslator
    url: http://httpbin.org/post
    content_type: application/json
    
    [test]
    type: hook
    translators: TestTranslator
    
    [TestTranslator]
    type: translator
    translator: hooky.translators.base.TestTranslator

This example configures Hooky to accept an incoming web hook at */hook/githubToPost* and pass the incoming data off to *http://httpbin.org/post*. It also accepts a hook at */hook/test* and uses the *TestTranslator* to parse the hook and return data to the caller.

You may define as many *translator* and *hook* sections as you wish, and you can mix-and match them as necessary. 

*In the future you will be able to list several translators for a single incoming webhook. It is for this reason that we break up the hook and translator sections. This is not yet implemented, but coming very soon!* 

## Translators

Hooky ships with a few default Translator objects that can be used for common web hook translations. Custom Translators can be built at any time and added in as well. Subclass *hooky.translator.base.BaseTranslator* and implement the missing methods appropriately, then just reference your translator in the config
file. Its that easy!

### hooky.translators.base.TestTranslator

#### Configuration Reference
**No cconfiguration parameters **

#### Usage
Accepts XML/JSON or URI arguments, parses them, and returns back to the caller a set of variable names that can be substituted into a template for the PostTranslator. For example, if you submit the [Github example JSON](https://help.github.com/articles/post-receive-hooks) and submit it to the TestTranslator hook:

    MacBook-Pro:hooky $ curl -X POST -d @test_data/sources/github.json http://localhost:8080/hook/test
    
    Results: Key Name => Key value
    {{after}} => 1481a2de7b2a7d02428ad93446ab166be7793fbb
    {{before}} => 17c497ccc7cca9c2f735aa07e9e3813060ce9a6a
    {{commits}} => [{u'committer': {u'username': u'octokitty', u'email': u'lolwut@noway.biz', u'name': u'Garen Torikian'}, u'added': [], u'author': {u'username': u'octokitty', u'email': u'lolwut@noway.biz', u'name': u'Garen Torikian'}, u'distinct': True, u'timestamp': u'2013-02-22T13:50:07-08:00', u'modified': [u'README.md'], u'url': u'https://github.com/octokitty/testing/commit/c441029cf673f84c8b7db52d0a5944ee5c52ff89', u'message': u'Test', u'removed': [], u'id': u'c441029cf673f84c8b7db52d0a5944ee5c52ff89'}, {u'committer': {u'username': u'octokitty', u'email': u'lolwut@noway.biz', u'name': u'Garen Torikian'}, u'added': [], u'author': {u'username': u'octokitty', u'email': u'lolwut@noway.biz', u'name': u'Garen Torikian'}, u'distinct': True, u'timestamp': u'2013-02 22T14:07:13-08:00', u'modified': [u'README.md'], u'url': u'https://github.com/octokitty/testing/commit/36c5f2243ed24de58284a96f2a643bed8c028658', u'message': u'This is me testing the windows client.', u'removed': [], u'id': u'36c5f2243ed24de58284a96f2a643bed8c028658'}, {u'committer': {u'username': u'octokitty', u'email': u'lolwut@noway.biz', u'name': u'Garen Torikian'}, u'added': [u'words/madame-bovary.txt'], u'author': {u'username': u'octokitty', u'email': u'lolwut@noway.biz', u'name': u'Garen Torikian'}, u'distinct': True, u'timestamp': u'2013-03-12T08:14:29-07:00', u'modified': [], u'url': u'https://github.com/octokitty/testing/commit/1481a2de7b2a7d02428ad93446ab166be7793fbb', u'message': u'Rename madame-bovary.txt to words/madame-bovary.txt', u'removed': [u'madame-bovary.txt'], u'id': u'1481a2de7b2a7d02428ad93446ab166be7793fbb'}]
    {{compare}} => https://github.com/octokitty/testing/compare/17c497ccc7cc...1481a2de7b2a
    {{created}} => False
    {{deleted}} => False
    {{forced}} => False
    {{head_commit.added}} => [u'words/madame-bovary.txt']
    {{head_commit.author.email}} => lolwut@noway.biz
    ...
    ...
    {{repository.private}} => False
    {{repository.pushed_at}} => 1363295520
    {{repository.size}} => 2156
    {{repository.stargazers}} => 1
    {{repository.url}} => https://github.com/octokitty/testing
    {{repository.watchers}} => 1
    
    MacBook-Pro:hooky $ 

### hooky.translators.web.PostTranslator

#### Configuration Reference
* **url**: The remote URL to post data to *(ie: http://httpbin.org/post)*
* **content_type**: The Content-Type header to pass along with the POST data *(ie: application/json)*
* **auth**: *(optional)* HTTP Auth information *(ie: my_user:my_password)*
* **auth_mode**: *(optional)* HTTP Auth Mode *(ie: basic)*
* **template**: The contents (in string form) of the template.
   
   This template will be used to generate the outbound webhook POST data. This option is passed to the *PostTranslator* automatically from the *Config* module. See the documentation for the *Config* module for how it finds and supplies this option.
   
#### Usage
Accepts XML/JSON or URI arguments, reads in a template file, and generates an outbound web hook to a remote service URL submitting the data as a POST body. The template itself is read in as a text file named ***translator_name*.tmpl**.

An example config file might look like this:

*config.ini*

    [general]
    templates: templates
  
    [githubToPost]
    type: hook
    translators: GithubToHttpbinPost
    
    [GithubToHttpbinPost]
    type: translator
    translator: hooky.translators.web.PostTranslator
    url: http://httpbin.org/post
    content_type: application/json
    
*templates/GithubToHttpbinPost.tmpl*

    {
       "committer":"{{head_commit.author.name}}",
       "id":"{{head_commit.id}}",
       "url":"{{repository.url}}"
    }

If you submit a POST hook from Github (or manually using the example data from Github):

    MacBook-Pro:hooky $ curl -X POST -d @test_data/sources/github.json http://localhost:8080/hook/githubToPost
    Results: OK
    MacBook-Pro:hooky $ 

The outbound webhook to *http://httpbin.org/post* looked like this:

    {
       "committer":"Garen Torikian",
       "id":"1481a2de7b2a7d02428ad93446ab166be7793fbb",
       "url":"https://github.com/octokitty/testing"
    }

### Template Syntax

The Translators supplied with Hooky all use the [Pystache](https://github.com/defunkt/pystache) template system to generate outbound data. This templating system was chosen because its extremly simple and fast ... but it may not be as configurable as some other systems. Third-party Translator objects may use their own template systems.

This system provides a very simple syntax for referencing variables pushed to our *inbound* web hook. For example, if you're inbound service submits the following JSON:

    {
      'user': {
        'name': 'bob',
        'email': 'bob@bob.com'
      }
    }

You can reference the fields using the *{{field}}* syntax like this:

     { 'date': '01/01/2013',
       'email': {{user.email}}
     }