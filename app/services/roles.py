ROLES=[
 {'id':'manager','name':'Aarav','title':'AI Company Manager','icon':'🧠','extension':'101','department':'Executive'},
 {'id':'project_manager','name':'Kabir','title':'Project Manager','icon':'📋','extension':'102','department':'Executive'},
 {'id':'product_manager','name':'Ishaan','title':'Product Manager','icon':'🧭','extension':'103','department':'Executive'},
 {'id':'developer','name':'Arjun','title':'Senior Developer','icon':'👨‍💻','extension':'104','department':'Engineering'},
 {'id':'code_reviewer','name':'Rohan','title':'Code Reviewer','icon':'🔍','extension':'105','department':'Engineering'},
 {'id':'tester','name':'Neha','title':'QA Tester','icon':'🧪','extension':'106','department':'QA'},
 {'id':'ui_ux','name':'Meera','title':'UI/UX Designer','icon':'🎨','extension':'107','department':'Design'},
 {'id':'database','name':'Dev','title':'Database Engineer','icon':'🗄️','extension':'108','department':'Engineering'},
 {'id':'devops','name':'Vihaan','title':'DevOps Engineer','icon':'🚀','extension':'109','department':'Infrastructure'},
 {'id':'security','name':'Aryan','title':'Security Analyst','icon':'🛡️','extension':'110','department':'Security'},
 {'id':'ml_engineer','name':'Aditi','title':'ML Engineer','icon':'🤖','extension':'111','department':'AI/ML'},
 {'id':'automation','name':'Kunal','title':'Automation Engineer','icon':'⚙️','extension':'112','department':'Automation'},
 {'id':'data_analyst','name':'Ananya','title':'Data Analyst','icon':'📈','extension':'113','department':'Data'},
 {'id':'data_entry','name':'Rahul','title':'Data Entry Executive','icon':'⌨️','extension':'114','department':'Data'},
 {'id':'researcher','name':'Tara','title':'Research Analyst','icon':'🔬','extension':'115','department':'Research'},
 {'id':'hr','name':'Priya','title':'HR Manager','icon':'👩‍💼','extension':'116','department':'People'},
 {'id':'email','name':'Riya','title':'Email Assistant','icon':'📧','extension':'117','department':'Communication'},
 {'id':'sales','name':'Vikram','title':'Sales Executive','icon':'💼','extension':'118','department':'Growth'},
 {'id':'marketing','name':'Sara','title':'Marketing Specialist','icon':'📣','extension':'119','department':'Growth'},
 {'id':'support','name':'Nisha','title':'Customer Support','icon':'🎧','extension':'120','department':'Support'},
 {'id':'documentation','name':'Aditya','title':'Technical Writer','icon':'📚','extension':'121','department':'Documentation'},
 {'id':'finance','name':'Karan','title':'Finance Assistant','icon':'💰','extension':'122','department':'Finance'},
 {'id':'compliance','name':'Simran','title':'Compliance Officer','icon':'⚖️','extension':'123','department':'Compliance'},
 {'id':'operations','name':'Om','title':'Operations Manager','icon':'🏢','extension':'124','department':'Operations'},
]
BY_ROLE={r['id']:r for r in ROLES}
BY_NAME={r['name'].lower():r for r in ROLES}
BY_EXTENSION={r['extension']:r for r in ROLES}
