# Paper Won

*AI 45% | Mindset 35% | Trading 20%*

![A packing checklist rendered as a 1-bit template for an e-ink tablet](template.png)

Do you keep a packing list in your Notes app that you rewrite from scratch every single trip? Do you have three versions of it, on three devices, all slightly different? Do you tick something off and then get up at 1am to check it again, because you don't actually believe yourself?

I've said yes to all three. So I built a system to fix it, and the system taught me something I did not expect about which of my tools I can actually trust.

## The setup

We leave for Iceland and the Faroes on **Aug 9**. Seven days on the Norwegian Star, 50 to 55F the whole time, hard wind, two shore excursions on open boats.

I have a Supernote. It's an e-ink tablet, the kind you write on with a pen. It has a folder called MyStyle, and any PNG you drop in there becomes a template you can write on. So instead of a fourth Notes file, I wrote a little renderer that turns a packing list into a template and put it on the tablet.

The input is a small JSON file. Sections, items, a star on the don't-skip ones. That's the whole contract. It renders to a PNG sized to the exact pixel grid of the screen, **1404 by 1872**, because if it doesn't match the panel natively the whole page comes out soft and blurry.

One detail I liked. E-ink wants pure black and white, so the file gets flattened to 1-bit, which drops it from about 250KB to **25KB** and makes it crisper. But 1-bit means every pixel gets thresholded at a cutoff, and any light gray hairline just silently disappears. You have to draw the faint lines darker than they look like they should be, so they survive the flattening.

Paper has physics. Screens pretend they don't.

Then I packed. Pen, tablet, tick tick tick.

## The loop

The tablet exports what you wrote to a folder in the cloud. A script finds the newest export, reads which boxes I ticked, and flips those same items to checked in a master file.

It read them back correctly. Eight items, all in Documents and Money, nothing else touched.

![The corner I actually filled in, read back an hour later](ticked.png)

Look at how I marked them. Some are checkmarks. Some are X's straight through the box. One is a lazy diagonal that runs outside the lines. A regex would choke on that. Counting dark pixels would too. It works because something with eyes looks at the page the way a person would, and I left that step alone on purpose instead of pretending I could code my way around handwriting.

A spec becomes paper. Paper becomes ink. Ink becomes state.

## The part I got wrong

The same trip also lives in a little web app I built. Itinerary, map, ports, and the same packing list, on my phone, works offline.

![The trip app, which works offline and forgets everything](pwa_map.png)

I have been ticking boxes in that app for two weeks. Feeling organized about it.

Then I went looking for those checks so I could compare them against the tablet, and there was nothing there. Zero checked items. Not one.

The app stores its checkboxes in **localStorage**, which is a bucket inside one browser on one device. It never leaves. It isn't in the repo, it isn't synced, it isn't backed up. Open the same link on my wife's phone and every box is empty. Clear my site data and two weeks of packing evaporates.

It gets worse. The checkboxes are keyed by position in the list, `bring0`, `bring1`, `bring2`. Add one item to the top and every saved tick slides down a row. Nothing errors. Nothing warns you. The list just quietly starts lying about what you packed, and you find out in an airport.

So I ran an experiment without meaning to. Two checklists, same trip.

The digital one, written in modern JavaScript, served over HTTPS, installable to my home screen, cannot survive me switching phones.

The paper one survived being written on, scanned, exported to PDF, uploaded, and read back an hour later with every mark intact.

The e-ink page is the most reliable storage in the entire system. That is not the sentence I expected to write.

## The pen beat the JSON

One more. My flight confirmation code was printed right on the template, because I wanted it offline and in my hands. Before the page went anywhere, I scribbled over it with the pen.

That scribble is a real redaction. No layer under it, no metadata, no undo. It's ink and it's gone.

The JSON file still had the code sitting in plain text. So did the clean copy of the template. The digital source was the leaky one and the paper copy was the safe one, which is backwards from how anybody assumes this works. I stripped it out before any of this got published.

## Don't just trade for profits

Norwegian Cruise Line Holdings pays its shareholders an onboard credit. Hold the shares through the sailing, send in the form, and a 7 to 14 day cruise comes with **$100** to spend on the boat.

[Here's the page.](https://www.nclhltd.com/investors/shareholder-benefits)

So I own NCLH. The cruise line is buying me drinks on my own vacation, for the crime of owning the company I was already handing money to.

And because I can't leave anything alone, I sold a **$20 covered call for September** against those same shares. Same hundred shares doing two jobs. They qualify me for the onboard credit, and they collect premium while they sit there.

That is not a trade idea and I'm not telling anyone to go buy NCLH. It's a hundred bucks and some premium. The point is the habit. Before you book the thing, spend five minutes checking whether the company you're about to pay will pay you back for being an owner. Airlines, cruise lines, hotels, retailers you shop at anyway. Some of them have programs like this sitting on an investor relations page that nobody reads.

Trading isn't only the P&L screen. I've counted shoe brands at my kid's basketball game and turned it into cash-secured puts. I bought CALM because eggs got stupid at the grocery store. This is the same muscle pointed at a vacation.

But I digress.

## What I'd take from this

Automate the grunt work, not the thinking. Finding the file and editing the list are mechanical, so let them be mechanical. The judgment call in the middle, the actual "is that a checkmark or a smudge," stays with something that can see.

And be honest about what holds state. I have a repo, a cloud, a web app, a service worker, and an offline cache, and the thing that reliably remembered what I packed was a piece of e-ink with pen marks on it.

If you build the whole system and never test which half survives a power cycle, you don't have a system. You have a demo.

The template generator and the read-back loop are open source in my skills repo if you want to point them at your own life.

~ Michael
