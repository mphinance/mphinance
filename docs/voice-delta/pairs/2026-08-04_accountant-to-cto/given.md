# Alt + Tab

*AI 45% | Business 30% | Mindset 25%*

My entire career is one long argument with the idea of typing a number twice.

It started with Alt + Tab. Invoice open in one window, ERP open in the other, me in the middle, reading a figure off the left screen and typing it into the right screen. That was the job. I was the integration. A human API made of coffee and resentment.

Nobody hires you to fix that. You fix it because you're bored and you're the one doing it.

## The ladder

Every step of my career was the same move, applied to a slightly bigger problem.

**Alt + Tab.** A person reads one screen and types into another. This is where most companies still live, and they'll tell you it's fine.

**Import and export.** Get a CSV out of one system and into the other. Suddenly an afternoon is twenty minutes. Everyone acts like you did a magic trick, and all you did was refuse to be a copy-paste function.

**OCR.** Now the machine reads the invoice instead of me. First time it worked I genuinely sat back in the chair.

**Automated email plus OCR.** Now the machine also *gets* the invoice. The vendor emails it, it gets read, it gets filed, nobody touches it. That's the first one that felt less like a shortcut and more like a system.

**Field capture for service work.** Skip the paper entirely. The tech in the field enters it once, on site, and it's born digital. This is the step where you stop automating data entry and start deleting the reason data entry existed.

**Now AI does the rest.** Which sounds like a bigger leap than it is. It's the same move. Find the human sitting in the middle of two systems retyping things, and get them out of the middle.

That's the whole career. Six rungs, one idea. And I got a fancier title every time somebody noticed that the thing I built on a Tuesday out of spite was now load-bearing.

## The part that actually made me a nerd

None of that made me a programmer. Work automation is a means to an end and the end is going home.

What made me a programmer was wanting to steal the tricks for my house.

First real nerdness was [Automate the Boring Stuff with Python](https://automatetheboringstuff.com/), which is free to read online and remains the single best on-ramp I've ever handed to somebody who says they can't code. It doesn't teach you computer science. It teaches you that the boring thing you do every Thursday is a script, and you're allowed to write it.

Then I found a MakeUseOf article called [How To Turn Your Raspberry Pi Into An Always-On Downloading Megalith](https://www.makeuseof.com/tag/how-to-turn-your-raspberry-pi-into-an-always-on-downloading-megalith/). Not "machine." **Megalith.** That's 2014 tech blogging and I miss it. A $35 computer, sipping power, running unattended, doing a job forever without me. That reframed the whole thing. Automation wasn't just a faster me. It was a thing that existed while I slept.

Then I found [Home Assistant](https://www.home-assistant.io/).

It was over for me.

## And then the house started trading

My lights have been able to turn green or red based on the market for years now. It's the dumbest possible use of a very serious tool and I would not give it up for money.

Recently it got worse, in the good way. I can push flow notifications into the lights. Something hits, the room changes color, and I look up before I look at a screen.

![My wall display. Gamma walls and the weather, on the same panel.](wall.png)

That's a wall panel in my house. Read the cards left to right. Top options flow. Regime and gamma. Trigger states. And then, sitting right next to the gamma walls, a card that tells me the sun went down at 5:14 and something is playing in the living room.

Twelve year old me typing invoice numbers into an ERP could not have told you what a gamma wall is. But he would have understood that screen perfectly, because it's the same thing he wanted: everything I need to know, in one place, without me going and getting it.

I'm building this into TraderDaddy Pro now. Same instinct, bigger room.

## Which brings me to the current rung

The newest tool on the ladder is Claude Projects, and most people are using it wrong in exactly the way I used to use folders wrong.

A project is not a labeled drawer for chats. It's a workspace that remembers. And the difference shows up in three habits.

**Connect your sources instead of pasting them.** I sync actual GitHub repos into the project and connect the accounts the work touches. When I ask it to check something, it reads my real code and my real inbox, not a summary I typed from memory. Pasting context every session is the Alt + Tab of AI. You're the integration again. Stop it.

**Keep one living document, not eleven.** One brief, edited forward. Resolved things get struck through, not deleted, so the history stays readable. If you have `brief-v2` and `brief-final` and `brief-FINAL-2`, the project is already dead, you just haven't noticed.

**Write handoffs to your future self.** When something's done, have it write down what happened and what's still open. Next session starts warm. This is just the field capture step again. Enter it once, at the moment you know it, instead of reconstructing it later from nothing.

And the one people miss: a project is where a one-off becomes a tool. A packing checklist I built for a trip turned into a general-purpose skill that now lives in a repo and works for any list. The project was the sandbox. The tool was the export. Watch for that moment.

## The honest part

I'll tell you where I got cocky.

I was very proud of having one source of truth for that trip, one data file feeding a phone app and a tablet template. Clean. Elegant. I said it out loud.

Then something went looking for the state and came back with nothing, and I found out I'd had two lists the whole time, quietly disagreeing, and the checkboxes I'd been ticking for two weeks were saved in exactly one browser on exactly one phone.

I fixed it tonight. Partially. The committed file now seeds the checkboxes so a fresh device shows real state, which is a genuine improvement and also not the same thing as done.

Which is the actual lesson under all six rungs. You don't get to declare the thing automated. You get to check whether it survives a power cycle, find out it doesn't, and go fix it again.

I've been doing this since Alt + Tab. It never stops being that.

But I digress.

~ Michael
