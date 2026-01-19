import os
from ranker import rank_resumes, extract_text


resume_folder = "resumes"

resume_files=[os.path.join(resume_folder,f) for f in os.listdir(resume_folder) if f.endswith('.pdf' )]


jd=open("job_description.txt","r",encoding="utf-8").read()

ranked=rank_resumes(resume_files,jd)

for file,score in ranked:
    print(file,"->",round(score,4))