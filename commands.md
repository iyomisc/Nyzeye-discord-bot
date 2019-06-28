# Nyzeye bot commands

Commands Specs for the Nyzeye bot.

## General syntax

`Nyzeye command parameter(s)`

Nyzeye commands **have** to be issued in the dedicated #channel or in PM with @Nyzeye.  
They will **not** work in any other channel and you'll get into trouble for spamming!

# Commands

## Base commands

## Verifiers commands

Allows you to passively monitor all of your Verifiers.  
Set your alerts once, and get an alert via PM every time one of your watched verifier goes down.
- Sends a DM if a verifier you watch falls from the cycle
- Sends a DM when a verifier you watch gets 10 failures in a row (around 10 min, avoids false positives)
- Only send a PM once. The alert is then auto-reactivated when the verifier goes up again.

### watch
*Short_id* or *Short_id1 Short_id2 Short_id3*

Adds a Verifier Short_id (or list of Short_id, separated by spaces) to watch.
If any of these Verifiers goes inactive, you'll get a DM (once, until you fix it)

You can watch several Verifiers by issuing several watch commands.  
Verifier has to be registered and active to be watched.

Ex: `Nyzeye watch abcd.1234`
Ex: `!watch abcd.1234`
Ex: `Nyzeye watch abcd.1234 abcd.1234 abcd.1234`


### Verifier unwatch
*Short_id* or *Short_id1 Short_id2 Short_id3*

Removes a Verifier Short_id (or list of Short_id, separated by spaces) from watch.

Ex: `Nyzeye unwatch abcd.1234`
Ex: `!unwatch abcd.1234`

### Verifier list

Lists all currently watched Verifiers, with their last known status (can be 2 to 3 min late) and their nickname.
Failing Verifiers are displayed in bold.

Ex: `Nyzeye list`
Ex: `!list`
