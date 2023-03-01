

from transformers import pipeline
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import re

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
ARTICLE = """all right let's move on to scotus here
0:02
so Ryan I'm really curious what you
0:04
think of this the Supreme Court is
0:06
officially hearing the student loan debt
0:08
relief case let's go and put this up
0:09
there on the screen it says you decent
0:11
summary of what the argument's for and
0:13
against are so if we will return to what
0:15
the actual plan was ten thousand dollars
0:18
in federal student loan debt is getting
0:19
canceled for those making less than 125
0:22
000 or households with less than 250 000
0:25
in income Pell Grant recipients who
0:27
receive more financial need would get an
0:29
additional 10 000 in debt forgiven
0:31
college students would qualify if their
0:33
loans were dispersed before July 1st of
0:35
2022 that made some 43 million people
0:38
eligible for the plan the White House
0:41
has said already that 26 million have
0:43
applied for the relief and 16 million
0:45
had already had relief approved
0:46
Congressional budget office said it
0:48
would cost about 400 billion over 30
0:51
years however
0:53
the problem is is that the current case
0:55
before the court involves a student
0:57
named Myra Brown ineligible for debt
1:00
relief because her loans are
1:01
commercially held and an additional
1:03
student his name is Alexander Taylor who
1:05
is eligible for just 10 000 not the full
1:08
20 000 because he didn't receive a Pell
1:10
get Grant they say the Biden
1:12
Administration did not go through the
1:14
proper process in enacting this plan a
1:17
Texas judge actually ruled on behalf of
1:20
the students rule to block the program
1:21
he said that the Biden admin did not
1:24
have clear authorization from Congress
1:26
to implement the program now this goes
1:28
to what the buy Administration actually
1:30
did they used something called the
1:31
heroes act the heroes Act was passed
1:34
after September 11 2001 which said that
1:36
you were going to initially it was
1:37
passed keep service members from being
1:39
worse off financially when they fought
1:41
wars in Afghanistan Iraq reasonable now
1:43
though it allows the Secretary of
1:45
Education to waive or modify the terms
1:47
of student loans in connection with a
1:49
national emergency so this ties
1:52
specifically to the covid-19 pandemic
1:54
because the Biden Administration in
1:56
court is arguing we are still in the
1:59
middle of a coveted National Emergency
2:00
but the president has said rhetorically
2:03
the pandemic's over we have rescinded as
2:05
I understand at title 42 what was
2:07
happening down at the border we were
2:08
using covet as a pretext to expel
2:10
migrants we have a new effectively
2:11
remain in Mexico policy that is in
2:14
effect so in many legal grounds Ryan uh
2:17
from eviction moratoriums to the border
2:20
the by demonstration is no longer trying
2:22
to argue that covet is a national
2:23
emergency but in the case of student
2:25
loan relief they are saying it's
2:27
National Emergency and I saw the
2:28
Secretary of Education this morning on
2:30
television was asked how can are you
2:33
really saying that it's a national
2:34
emergency in court and not a National
2:36
Emergency to the American people he said
2:38
yes that's what we were saying I said
2:40
well that's going to be interesting
2:42
before the court they also haven't yeah
2:43
they also have an add-on argument which
2:45
I which I think is fair right which says
2:48
that the student loan crisis was badly
2:51
exacerbated
2:52
by the pandemic so even if you stipulate
2:55
yes that legally and actually the
2:59
pandemic is over let's just stipulate
3:01
for the for this for the for the
3:03
argument's sake
3:04
the crisis still happened because of
3:07
that and the law allows
3:09
us to respond to a crisis that happened
3:11
during uh during that time and because
3:14
of the pause and because of the economic
3:17
the pause and Loan repayments and
3:19
because of the economic shock that came
3:21
from the pandemic so many people losing
3:22
losing their jobs uh that you could say
3:26
that there are many people who
3:27
desperately need this and I think that's
3:29
actually true I don't think that that's
3:31
kind of playing games with stuff because
3:33
you have so many people who are now used
3:37
to not making that three to six hundred
3:39
dollar payment which they kept extending
3:41
and extending right like 25 months their
3:43
balance if they had continued paying
3:45
over the last three years would be
3:47
substantially lower even though they got
3:49
up they got a pause on interest rates uh
3:51
than it than it is now so now all of a
3:53
sudden if the court rules you know with
3:56
these with these uh Angry borrowers you
3:59
now are going to all of a sudden have to
4:00
start paying this money now I actually
4:02
don't think they will I think Biden
4:03
would just keep in definitely pausing it
4:05
for everybody which is hilarious like
4:07
wait a minute so you can't cancel 10
4:11
basically cancel all of it forever okay
4:14
that's weird uh so I think that make
4:16
making that case that look this was a
4:19
crisis created by the pandemic should
4:21
allow you to use the law around the
4:23
pandemic so that's if I were and I've
4:26
heard them make versions of that
4:27
argument we'll see it's going to be this
4:29
morning right so we'll see we'll see how
4:31
that goes yeah just a couple of hours
4:33
from where we're actually not that far
4:34
from where we're filming right now uh
4:35
and one of the things that the justices
4:36
are expected to focus on a couple of
4:38
things number one is whether the states
4:40
and the borrowers even have a right to
4:42
sue over the plan in the first place
4:43
this is called standing if they don't
4:45
then they can just say you don't have
4:47
standing to sue for us before The
4:48
Supreme Court so Ergo the decision
4:50
stands and the plan can go ahead the
4:52
other thing that what they have to prove
4:53
is that the states and the borrowers
4:55
have to show that they are financially
4:57
harmed right by the plan I mean on the
4:59
borrowers part that's not hard to
5:01
imagine but on the states parts that are
5:02
joining the suit that might be and then
5:04
otherwise they are also going to
5:06
question exactly whether the heroes act
5:08
even gives a buy had been the power to
5:10
enact the plan now look a lot of this is
5:12
partisan too and I would say uh based on
5:15
from what I've people I've talked to
5:16
Kavanaugh is going to be one of the
5:17
swinger votes and that's why because if
5:20
we go back to the original eviction
5:21
moratorium Nation moratorium was
5:23
challenged before The Supreme Court
5:24
Kavanaugh said look legally I don't
5:27
think you guys have standing that or I
5:29
don't think you guys have a foot to
5:31
stand on that said from what I have
5:33
looked at we still have a coveted
5:35
emergency I don't want to kick people
5:37
out of their homes so I'm gonna punt it
5:39
to you Congress you have 60 days to
5:42
extend the eviction moratorium the bite
5:44
Administration doesn't do it Congress
5:45
doesn't do it and then it ends up before
5:47
the stream Supreme Court again he's like
5:49
look I told you you had 60 days you
5:50
don't have 60 days anymore and this came
5:52
all the way down to the National
5:53
Emergency declaration so one of the
5:55
reasons why I think it will be very
5:57
important and likely uh it's very likely
5:59
to get struck down at the court um
6:01
possibly not even just six three it
6:03
could even be 7-2 from what I understand
6:05
is that National the student loan one
6:07
this specifically is going to rest on
6:09
the National Emergency declaration and
6:11
the ability to use the heroes act with
6:12
covid as a pretext and you know irony is
6:15
Ryan as I understand it they had a much
6:16
easier way to cancel all this debt
6:18
nobody asked them to go through the
6:20
heroes act there's no reason why they
6:21
had to it's probably the most legally
6:23
precarious out of all of them that they
6:25
chose right they could have used the
6:26
higher education acts which has some
6:28
Provisions that would that give the
6:29
education department a lot more a lot
6:32
more flexibility which is what Trump
6:33
used you know in the very early stages
6:36
to pause this before they uh you know
6:39
enacted you know before they amended the
6:40
heroes legislation so one possibility
6:44
could be that the Supreme Court could
6:46
use the Higher Education Act to legalize
6:49
it yes but you don't have like you don't
6:51
have to rely on the reasoning of the
6:54
litigants in your ruling you're the
6:56
Supreme Court you can supremely do
6:58
whatever he wants John Roberts showed
7:00
that with the Affordable Care Act
7:02
remember they said this is a this is a
7:04
mandate so well you can't do a mandate
7:05
uh and Robert said well actually it's
7:07
not a mandate it's a tax yeah and so he
7:10
rewrote the reasoning for the law
7:11
literally to then Legalize It
7:13
constitutionally yes and so they they
7:16
could do that and so it'll be
7:18
interesting to watch to see if the
7:20
solicitor general for the White House
7:21
says
7:22
even if you don't believe any of this
7:24
Heroes act justification and but you
7:26
want to protect this should do you
7:28
should you know here here's another
7:30
argument that you could use if you if
7:32
you chose to I also think the standing
7:34
is interesting but it's it's shot
7:36
through with a lot of politics it's hard
7:39
to see how these students
7:41
are being harmed because they're paying
7:44
they're paying no matter what like not
7:47
being part of a program is is definitely
7:49
not harm yeah like if and so
7:54
like it may be sad like you I feel bad
7:56
that you didn't qualify for this thing
7:58
that's unfortunate but it doesn't make
8:01
you worse off than you currently are I'm
8:03
not sure because the problem was is that
8:05
there were all these suits and the one
8:06
suit that I clearly people being harmed
8:08
are who debt services
8:10
like they're people who literally are
8:12
payment collectors they are materially
8:15
being harmed they actually could argue
8:16
that as I understand that that case
8:18
didn't end up uh moving forward they the
8:20
Challenger stop this would be the best
8:22
way to extract the most sympathetic not
8:24
the most sympathetic certainly uh that
8:25
said as I from what I have heard I could
8:28
be completely wrong of some of the Court """

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

