# Alt + Tab

*Trading 35% | AI 35% | Mindset 30%*

![A packing checklist rendered as a 1-bit template for an e-ink tablet](template.png)

I spent years as an accountant finding people who type the same number into two different screens, and getting them out of the middle. That's the whole career. Everything after it is that, with a bigger budget and a worse title.

It started with Alt + Tab. Invoice open in one window, ERP open in the other, me in between, reading a figure off the left screen and typing it into the right one. That was the job. I was the integration.

## The ladder

**Alt + Tab.** A person reads one screen and types into another. A lot of companies still live here.

**Import and export.** Get a CSV out of one system and into the other, and an afternoon becomes twenty minutes.

**OCR.** Now the machine reads the invoice instead of me. First time it worked I sat back in the chair.

**Automated email plus OCR.** Now the machine also *gets* the invoice, which was the first one that felt like a system instead of a shortcut, mostly because it kept working on days I wasn't there.

**Field capture on site.** Skip the paper. The tech enters it once, in the field, and it's born digital. This is the good rung. You're not making data entry faster anymore, you're deleting the reason anybody had to do it.

And now AI does the rest, which sounds like a bigger jump than it is. Same move, better tools. Find the human sitting in the middle of two systems retyping things, get them out of the middle.

## How I got infected

None of that made me a programmer. I automated work stuff so I could leave at 4:30.

What made me a programmer was wanting to steal the tricks for my house. First real nerdness was [Automate the Boring Stuff with Python](https://automatetheboringstuff.com/), which is free to read online and is still the thing I hand anybody who says they can't code.

Then I found a 2014 MakeUseOf article called [How To Turn Your Raspberry Pi Into An Always-On Downloading Megalith](https://www.makeuseof.com/tag/how-to-turn-your-raspberry-pi-into-an-always-on-downloading-megalith/), and yes it says Megalith, not machine, which is the kind of tech blogging I miss, but I digress. A $35 computer running unattended forever. That's when it clicked. Automation isn't me going faster, it's a thing running at 3am while I'm asleep.

Then I found [Home Assistant](https://www.home-assistant.io/).

It was over for me.

My lights have been able to turn green or red based on the market for years now. Dumbest possible use of a very serious tool and I would not give it up for money. Now I can push flow notifications into the lights, so something hits, the room changes color, and I look up before I look at a screen. I'm wiring that into TraderDaddy Pro, the platform I build screeners for.

![My wall display. Gamma walls and the weather, on the same panel.](wall.png)

That's a wall panel in my house. Options flow, regime, gamma, trigger states, and then one card over, a thing telling me the sun is down and comes back at 5:14 and something is playing in the living room.

The accountant typing invoice numbers into an ERP couldn't have told you what a gamma wall is. He'd have understood that screen fine, though, because it's the same thing he wanted. Everything in one place, without me going and getting it.

## The boat is also a position

We fly out for Iceland and the Faroes on Aug 7 and board the Norwegian Star on the 9th. Seven days, 45 to 55F the entire time, hard wind, two shore excursions on open boats.

Norwegian Cruise Line Holdings gives shareholders an onboard credit, and I own NCLH, so the cruise line is buying me drinks on my own vacation for the crime of owning the company I was already handing money to. Actual terms, since "go check the IR page" is useless without them: you need **100 shares at the time of sailing**, the credit is **per stateroom** and not per person, and the request has to be in **at least fifteen days before you sail**. It's $50 for sailings of 6 days or less, **$100 for 7 to 14 days**, $250 for 15 or more, and it won't cover gratuities or excursions you already booked. [Here's the page.](https://www.nclhltd.com/investors/shareholder-benefits)

And because I can't leave anything alone, I sold a September $20 covered call against those same shares, with the stock in the high teens. Same hundred shares doing two jobs. The normal path is the boring one: I sail Aug 9, the call doesn't expire until September, so the credit is already banked and the only thing at stake afterward is whether the shares get called away above $20, which I'd take. The hole is early assignment. If someone calls those shares away before Aug 9 I don't own stock at time of sailing and the credit goes with it. NCLH pays no dividend so that's unlikely, but unlikely isn't can't.

I'm not telling anybody to buy NCLH. I've counted shoe brands at my kid's basketball game and turned it into cash-secured puts, and I bought CALM because eggs got stupid at the grocery store. Same muscle, pointed at a vacation.

Anyway. The packing list.

## The packing list

Here's the part I should have led with. When I'm actually packing, I write on paper. Not out of nostalgia. I'm walking around the house with my arms full, and a pen is faster than unlocking a phone, finding the app and scrolling to the right line. I think most people are the same way, they just don't say it out loud because paper feels like a step backward.

I used Google Keep for this before and the list itself was fine. What I hated was that Keep made checking it a separate errand. Pack for an hour, then sit down later and go tell the app what I did. That's Alt + Tab again. I'd built a career on deleting exactly that motion and I was doing it to myself on a Tuesday night with a suitcase open.

So I didn't want a better app. I wanted the paper I was already going to use to file its own paperwork.

I have a Supernote, an e-ink tablet you write on with a pen. It has a folder called MyStyle, and any PNG you drop in there becomes a template. So instead of a fourth Notes file I wrote a renderer that turns a packing list into a template and put it on the tablet.

The input is a small JSON file. Sections, items, a star on the don't-skip ones. It renders at the exact pixel grid of the panel, 1404 by 1872, because if it doesn't match natively the whole page comes out soft.

One detail I liked. E-ink wants pure black and white, so the file gets flattened to 1-bit, which takes it from about 230KB to 25KB and makes it sharper. But 1-bit means every pixel gets thresholded at a cutoff, and any light gray hairline just silently disappears. So the greys in my renderer are set darker than they look like they should be, specifically so they survive the flattening.

Then I packed. Pen, tablet, tick tick tick.

## The loop

The tablet exports what you wrote to a folder in the cloud. A script finds the newest export, Claude reads which boxes I ticked, and a second script flips those items to checked in a master file.

![The corner I actually filled in, read back an hour later](ticked.png)

Eight items back, correctly, nothing else touched. Look at how I marked them though. Most are X's straight through the box, one is a lazy diagonal running outside the lines. A regex would choke. Counting dark pixels would too.

That middle step is the only part of this I deliberately did not automate. Handwriting is a judgment call, and I'd rather admit that than write four hundred lines pretending it isn't.

Which is the whole thing, really. I spent years pulling people out of the middle of two systems, and the answer here was not to pull me out. I like being in the middle of this one. I like the pen. The job was to make sure that the twenty seconds I spend with a pen is the *only* time I have to think about it, instead of the down payment on a transcription chore later.

## Where I got cocky

Now the part where I proved I hadn't learned it yet. The same trip also lives in a little web app I built. Itinerary, map, ports, offline, on my phone.

![The trip app, which works offline and forgets everything](pwa_map.png)

I told myself I had one source of truth. One data file feeding a phone app and a tablet template. Clean, elegant, and I said it out loud, which should have been the tell.

I'd been ticking boxes in that app for two weeks. Then I went looking for those checks so I could compare them against the tablet, and there was nothing there. Zero checked items, not one.

The app stores its checkboxes in localStorage, which is a bucket inside one browser on one device. It never leaves. Not in the repo, not synced, not backed up. Open the same link on my wife's phone and every box is empty.

It gets worse, because the checkboxes are keyed by their position in the list. `bring0`, `bring1`, `bring2`. Add one item to the top and every saved tick slides down a row. No error, no warning, nothing. The list just starts lying about what you packed and you find out about it in an airport.

And the two lists were never the same list anyway. The tablet template has 49 items on it. The `bring` array feeding the phone has 11. I'd been calling that one source of truth for weeks.

I fixed it that night, sort of. The committed file now seeds the checkboxes, so a fresh device shows real state instead of nothing. It currently seeds exactly one item, because I did the plumbing and not the data, and a local tap still overrides the committed file forever on that device. Genuine improvement. Not the same thing as done.

## The scribble that wasn't enough

My flight confirmation code was printed on the copy of the template I actually wrote on, because I wanted it offline and in my hands. Before that page went anywhere I scribbled over the code with the pen and felt good about it.

Then I looked at the scan. The scribble covered the code, but you could still read the tail end of it around the edges of my own ink. So the ticked-boxes image further up this post has a black rectangle sitting on top of my pen scribble, put there in software, because the analog redaction I was proud of did not hold. The JSON file still had the code sitting in plain text too, and that got stripped before any of this got published.

So the paper held the state better than the app, and the ink held the secret worse than I thought.

## What I'd take from this

Build around how you actually behave, not how you wish you did. I was never going to stop grabbing a pen while I packed. Every version of this that started with "and then I open the app" was going to lose to the pen, because the pen was already in my hand. So the automation goes on the *other* side of the pen, where the boring part lives.

Automate the grunt, not the judgment. Finding the file and editing the list are mechanical, so let them be mechanical. The "is that a checkmark or a smudge" call stays with something that can see, and that's the design, not a gap in it.

And be honest about what holds state. I have a repo, a web app and an offline cache, and the thing that reliably remembered what I packed was a piece of e-ink with pen marks on it.

If you build the whole system and never test which half survives a power cycle, you don't have a system. You have a demo.

*The template generator and the read-back loop are open source at [github.com/mphinance/alpha-skills](https://github.com/mphinance/alpha-skills) if you want to point them at your own life.*

~ Michael
