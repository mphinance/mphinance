TITLE: From Accountant to CTO - It Started With Alt + Tab
SUBTITLE: Trading 15% | AI 45% | Mindset 40%
AUDIENCE: everyone

- 
- 
[caption] Claude made a Supernote packing listMy mom has been calling me all week to make sure I’ve got everything packed and ready for a trip. 42 years have I been on this Earth after being squeezed from her womb, and still she’s incessant. This is my answer to the next 5 calls as well.

I spent years as an accountant, and immediately one of my biggest pet peeves was watching people double enter the same information in multiple windows, switching back and forth.

My automation started with Alt + Tab. Invoice open in one window, ERP open in the other, me in between, reading a figure off the left screen and typing it into the right one. That was the job. I was the integration.

## The ladder

- Alt + Tab. A person reads one screen and types into another. A lot of people still live here.

- Import and export. Get a CSV out of one system and into the other, and an afternoon becomes twenty minutes. Python can write CSVs too.

- OCR. Now the machine reads the invoice instead of me. First time it worked I sat back in the chair.

- Automated email plus OCR. Now the machine also gets the invoice, which was the first one that felt like a system instead of a shortcut, mostly because it kept working on days I wasn't there.

- Field capture on site. Skip the paper. The tech enters it once, in the field, and it's born digital. This is the good rung. You're not making data entry faster anymore, you're deleting the reason anybody had to do it.

And now AI does the rest, which sounds like a bigger jump than it is. Same move, better tools. Find the human sitting in the middle of two systems retyping things, get them out of the middle.

Subscribe now

## How I got infected
None of that made me a programmer. I automated work stuff so I could leave at 4:30.

What made me a programmer was wanting to steal the tricks for my house. First real nerdness was Automate the Boring Stuff with Python, which is free to read online and is still the thing I hand anybody who says they can't code.

Then I found a 2014 MakeUseOf article called How To Turn Your Raspberry Pi Into An Always-On Downloading Megalith, and yes it says Megalith, not machine, which is the kind of tech blogging I miss, but I digress. A $35 computer running unattended forever. That's when it clicked. Automation isn't me going faster, it's a thing running at 3am while I'm asleep.

Then I found Home Assistant.

It was over for me.

My lights have been able to turn green or red based on the market for years now. Dumbest possible use of a very serious tool and I would not give it up for money. Now I can push flow notifications into the lights, so something hits, the room changes color, and I look up before I look at a screen. I'm wiring that into TraderDaddy Pro, the platform I build screeners for.

- 
- That's a wall panel in my house - still very much a WIP since Art hasn’t gotten to make it beautiful yet. Options flow, regime, gamma, trigger states, and then one card over, a thing telling me the sun is down and comes back at 5:14 and something is playing in the living room.

The accountant typing invoice numbers into an ERP couldn't have told you what a gamma wall is. He'd have understood that screen fine, though, because it's the same thing he wanted. Everything in one place, without me going and getting it.

## The boat is also a position
We fly out for Iceland next week for a cruise and to catch the total solar eclipse, and my mom won’t stop calling me to make sure I’ve got XYZ printed, waterproof this and that.

Before I forget - little side track here that I left a note about yesterday:

Norwegian Cruise Line Holdings gives shareholders an onboard credit. Actual terms, since "go check the IR page" is useless without them: you need 100 shares at the time of sailing, the credit is per stateroom and not per person, and the request has to be in at least fifteen days before you sail. It's $50 for sailings of 6 days or less, $100 for 7 to 14 days, $250 for 15 or more, and it won't cover gratuities or excursions you already booked. Here's the page.

And because I can't leave anything alone, I sold a September $20 covered call against those same shares, with the stock in the high teens. Same hundred shares doing two jobs. The normal path is the boring one: I sail Aug 9, the call doesn't expire until September, so the credit is already banked and the only thing at stake afterward is whether the shares get called away above $20, which I'd take. 

I'm not telling anybody to buy NCLH. I've counted shoe brands at my kid's basketball game and turned it into cash-secured puts, and I bought   because eggs got stupid at the grocery store.

Anyway. The packing list.

## The packing list
The part I should have led with, but I saw a butterfly. When I'm actually packing, I write on paper. Not out of nostalgia. I'm walking around the house with my arms full, and a pen is faster than unlocking a phone, finding the app and scrolling to the right line. I think most people are the same way, they just don't say it out loud because paper feels like a step backward.

I used Google Keep for this before and the list itself was fine. What I hated was that Keep made checking it a separate errand. Pack for an hour, then sit down later and go tell the app what I did. That's Alt + Tab again. I'd built a career on deleting exactly that motion and I was doing it to myself on a Tuesday night with a suitcase open.

So I didn't want a better app. I wanted the paper I was already going to use to file its own paperwork.

I have a Supernote, an e-ink tablet you write on with a pen. It has a folder called MyStyle, and any PNG you drop in there becomes a template. So instead of a fourth Notes file I wrote a renderer that turns a packing list into a template and put it on the tablet. Thanks Claude.

The input is a small JSON file. Sections, items, a star on the don't-skip ones. It renders at the exact pixel grid of the panel, 1404 by 1872, because if it doesn't match natively the whole page comes out soft.

Then I packed some paperwork from the printer. Pen, tablet, tick tick tick.

## The loop
The tablet exports what you wrote to a folder in the cloud. A script finds the newest export, Claude reads which boxes I ticked, and a second script flips those items to checked in a master file.

- 
- Eight items back, correctly, nothing else touched. Look at how I marked them though. Most are X's straight through the box, one is a lazy diagonal running outside the lines. A regex would choke. Counting dark pixels would too.

I like being in the middle of this one. I like the pen. The job was to make sure that the twenty seconds I spend with a pen is the only time I have to think about it, instead of the down payment on a transcription chore later.

## I couldn’t stop there
The same trip also lives in a little web app I built. Itinerary, map, ports, offline, on my phone - and so I can show my mom my completed check boxes later.

- 
- I told myself I had one source of truth. One data file feeding a phone app and a tablet template. Clean, elegant, and I said it out loud, which should have been the tell.

## What I'd take from this
Build around how you actually behave, not how you wish you did. I was never going to stop grabbing a pen while I packed. Every version of this that started with "and then I open the app" was going to lose to the pen, because the pen was already in my hand. So the automation goes on the other side of the pen, where the boring part lives.

Automate the grunt, not the judgment. Finding the file and editing the list are mechanical, so let them be mechanical. The "is that a checkmark or a smudge" call stays with something that can see.

The template generator and the read-back loop are open source at https://github.com/mphinance/alpha-skills/tree/main/skills/supernote-mystyle if you want to point them at your own life.

~ Michael
