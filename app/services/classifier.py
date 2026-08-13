from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from .roles import BY_NAME
DATA=[
 ('build code api website backend frontend python react fix bug code','developer'),('review code architecture refactor clean maintainability','code_reviewer'),('test qa defect regression verify testcase browser','tester'),
 ('ui ux design wireframe responsive interface prototype','ui_ux'),('database sql schema table query index migration','database'),('deploy docker ci cd cloud hosting release','devops'),('security owasp vulnerability auth encryption permissions','security'),
 ('machine learning model dataset train inference sklearn ai ml','ml_engineer'),('automation automate repetitive workflow browser bot process','automation'),('analyze data kpi trends metrics report statistics','data_analyst'),('data entry csv excel records spreadsheet form typing','data_entry'),
 ('research compare competitor investigate evidence findings','researcher'),('hire candidate interview recruiter onboarding resume hr','hr'),('email mail reply message invitation followup send','email'),('sales lead client proposal crm deal prospect','sales'),('marketing campaign seo content social promotion','marketing'),
 ('support ticket complaint helpdesk customer issue resolution','support'),('documentation readme guide manual api docs technical writing','documentation'),('invoice budget expense revenue payment finance','finance'),('compliance privacy policy legal regulation audit','compliance'),('operations workflow sla process coordination daily','operations'),
 ('project timeline sprint milestone task dependency agile scrum','project_manager'),('product roadmap user story requirements backlog priority','product_manager')]
class Router:
 def __init__(self):
  self.p=Pipeline([('tfidf',TfidfVectorizer(ngram_range=(1,2))),('clf',LogisticRegression(max_iter=1200))]);x,y=zip(*DATA);self.p.fit(x,y)
 def classify(self,text):
  low=text.lower()
  for name,role in BY_NAME.items():
   if low.startswith(name+' ') or low.startswith(name+',') or (' '+name+' ') in (' '+low+' '): return role['id']
  return str(self.p.predict([text])[0])
router=Router()
