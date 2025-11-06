### RCS (Resume Creation System)
Finding the right job, determining if you're the right fit, tailoring a resume... such a drag! With this prototype, all you have to do it save some jobs on LinkedIn, write everything you know about yourself into a text file, and let the agent cook!

#### Step 0: Installations

```
pip install -r requirements.txt
```

#### Step 1: Save Jobs on LinkedIn

Go to your LinkedIn account and browse around for jobs your like, then save a couple.

#### Step 2: Experience Dump

Write about all of your experience in as much detail as possible into `experience.txt`.

#### Step 3: Set up LinkedIn login information and OpenAI API Key

Create a .env and add the following variables:
```
LINKEDIN_EMAIL
LINKEDIN_PASSWORD
OPENAI_API_KEY
```

#### Step 4: Collect Job Descriptions

Run the LinkedIn scraper to retrieve the job descriptions from your saved list.

```
python simple_scraper.py
```

#### Step 5: Run the analysis

Finally, let the model choose which job is the best fit, and write you a nice LaTeX resume.

```
python resume_creation_agent.py
```


