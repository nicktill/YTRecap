

from transformers import pipeline
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import re

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
ARTICLE = """0:00
The Joe Rogan Experience you heard Woody
0:03
Harrison on SNL did you see that
0:06
immediately after Woody Harrelson had
0:09
that monologue on SNL where he's joking
0:11
around
0:12
about a drug company forcing you to take
0:15
their drug right after it the next day
0:18
there's all these hit pieces like like
0:20
they were timed like this pit piece and
0:23
fox is a hit piece in Vanity Fair it was
0:25
a hit piece calling him an anti-vaxxer
0:27
and a stoner and sucked on Cheers
0:30
conspiracy theories he's pushing
0:33
conspiracy theories no he's no no no no
0:35
that's not what he's doing he's a joke
0:37
monologue on SNL about something that
0:40
makes people laugh because you can kind
0:42
of make a weird comparison to those two
0:44
that's the only reason why the joke
0:45
works yeah the only reason why it works
0:48
is because people are thinking it like
0:50
so for you guys to come out and say like
0:52
oh conspiracy if you're saying doesn't
0:54
no it's jokes about a possible
0:58
conspiracy theory
1:00
and the one that he's describing isn't
1:03
having it's not even a real one he's
1:05
making a joke about what the real one
1:07
was like
1:08
maybe not the best joke maybe not the
1:10
best delivery but the fact that that got
1:13
this immediate response where all these
1:16
people defend the pharmaceutical
1:18
companies they're all jumping in and
1:20
defending them like in unison they're
1:23
all anti-vaxxer stoner
1:26
and you know instead of saying it sucked
1:28
or instead of saying hey stick to acting
1:30
instead you know no it's like
1:32
they all wanted to jump in to defend the
1:35
vaccine
1:36
they all wanted to jump in and defend
1:37
the pharmaceutical companies from this
1:40
anti-vaxxer stoner
1:43
actor who's talking it's just
1:45
interesting that they all take that
1:47
route
1:48
I get criticized in the monologue but
1:51
all taken that route that's an anti-vasc
1:54
conspiracy Jerry look is it
1:56
no it's he's joking about a way things
1:59
went down yeah like there's a lot to
2:01
what he's saying like forcing you to
2:03
take their drug like that kind that kind
2:05
of was happening and if you weren't
2:07
getting forced you were certainly
2:08
getting coerced you're getting urged on
2:10
by the government
2:12
there was probably a commercial for a
2:14
medicine right after that yeah probably
2:15
right away right away
2:17
it's not like they're not spending money
2:19
on all this stuff like like why are we
2:22
pretending
2:24
and so when he makes that joke
2:29
and he talks about them buying all the
2:31
media
2:33
and then all the media responses if
2:35
they've been bought and paid for that's
2:36
pretty wild
2:38
there's so many articles written about
2:40
them like right away yeah I was like
2:42
this is crazy I always look at both
2:44
sides and CNN had it but also CNN is
2:49
owned by the same company that owns SNL
2:51
So It's tricky because they don't want
2:53
to make them look bad
2:55
but they you know
2:58
angled it like it was him yeah even
3:00
though what we know is that these
3:03
scripts are approved days in advance
3:04
yeah they had to prove that unless you
3:06
went out and Dave chappelled it
3:08
yeah he he didn't Dave had two different
3:11
monologues
3:12
e Dave ran one monologue by everybody
3:15
and killed and they're like this is
3:16
great then he goes on Friday does a
3:19
whole separate one oh
3:22
God bless him
3:24
God bless him because Woody Harrelson
3:26
did that God bless him but you know look
3:30
the fact that everybody jumped in like
3:31
that was just very interesting """

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('omw-1.4')

def preprocess_text(text):

    # Define regex pattern to match times
    pattern = r'\b\d{1,2}:\d{2}\b'

    # Remove time stamps from text
    text = re.sub(pattern, '', text)

    # Remove line breaks
    text = text.strip()
    
    # Tokenize the text into individual words
    tokens = word_tokenize(text)
    
    # Remove stop words from the text
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [token for token in tokens if token not in stop_words]
    
    # Lemmatize the words in the text
    lemmatizer = WordNetLemmatizer()
    lemmatized_tokens = [lemmatizer.lemmatize(token) for token in filtered_tokens]
    
    # Join the lemmatized tokens back into a single string
    preprocessed_text = ' '.join(lemmatized_tokens)
    
    return preprocessed_text

print(preprocess_text(ARTICLE))
print(summarizer(preprocess_text(ARTICLE), max_length=200, min_length=30, do_sample=False))

