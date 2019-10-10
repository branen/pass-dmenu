---
title: pass-dmenu(1)
date: 21 Sep 2019
lang: en-US
panflute-filters: filter
---

# Name

pass-dmenu - an ergonomic UI for Password Store


# Synopsis

`pass-dmenu` {`clip`, `type`} [*dmenu args*]...


# Description

`pass-dmenu` is a [`dmenu`]-based UI for [Password Store] that uses predictive ordering and integrations with [`xdotool`] and [`pass-otp`] to reduce considerably the number of keystrokes required to use a password.

It is especially effective where sets of related passwords tend to be addressed in sequence.

## Actions

The first argument to `pass-dmenu` must be the action to be performed with the selected password:

`clip`

: Copy the selected password to the clipboard (using [`xclip`]).

`type`

: "Type" the selected password (using [`xdotool`]).

(`pass-dmenu clip` clears the clipboard after one paste or `$PASSWORD_STORE_CLIP_TIME` seconds.)

## Additional arguments

Any additional arguments to `pass-dmenu` are passed directly to [`dmenu`].

## One-time password support

If a password value begins with `otpauth://`, [`pass-otp`] will be used to generate a one-time password, which will then be *clipped* or *typed* as usual.


# Predictive ordering

[`dmenu`] provides two mechanisms by which to select an element from a list of options:
filtration (based on substring match) and sequential navigation.
Because [`dmenu`]'s sequential navigation always starts with the first filtered element, elements near the head of the list tend to require fewer keystrokes to select than elements elsewhere in the list.
Thus, if we promote to the head of the list the elements that are likeliest to be selected in a given invocation, we can reduce the number of keystrokes required to select them.

`pass-dmenu` begins with a list of password names in lexicographic order and performs this promotion using:

- a set of manually defined, regex-based rules and
- the password name selected in the most recent [prior] `pass-dmenu` invocation.

## Rulesets

Rules for a password store are defined in the file `.pass-dmenu.rules` at the root of the password store.
This ruleset is a JSON-encoded list of rules, where each rule is a single-element dictionary mapping a regular expression to a list of regular expression templates.
(Specifically, these are [Python regular expressions] and [Python format string templates].)

For convenience, single-element template lists can be abbreviated by their element.

In short, the schema is:
```
RuleSet: List[
    SingleElementDict[
        MatcherRegex,
        Union[PickerRegexTemplate, List[PickerRegexTemplate]]
    ]
]
```

Roughly, each rule maps from "what was selected most recently" to "what is likeliest to be selected next."

## Evaluation

Each *MatcherRegex* is evaluated against the most-recently-used password name (or the empty string, if there is no most-recently-used password).
When there's a hit, the resulting *MatchGroup* is interpolated into each *PickerRegexTemplate*, resulting in a *PickerRegex*.
(Regex control characters appearing in the *MatchGroup* are escaped as necessary.)

```
Match: fn[MostRecentlyUsedPasswordName, MatcherRegex] -> Optional[MatchGroup]
Interpolate: fn[MatchGroup, PickerRegexTemplate] -> PickerRegex
```

This process is applied to each rule in the ruleset, ultimately resulting in a list of  *PickerRegex* objects, ordered as they appear in the original JSON document:

```
Evaluate: fn[RuleSet, MostRecentlyUsedPasswordName] -> List[PickerRegex]
```

## Promotion

Once the evaluation process is complete, `pass-dmenu` initializes two lists:

- a *residual* list is initialized with all the names in the password store, sorted lexicographically, and
- a *promoted* list is initialized with no elements.

Starting with the first *PickerRegex*, `pass-dmenu` considers each element in the residual list, from head to tail.
Each time it encounters an element that matches the current *PickerRegex*, that element is moved from its position in the residual list to the tail of the promoted list.
This process repeats for each *PickerRegex*.
Once it is complete, any elements that remain in the residual list are moved in order to the promoted list, and the promoted list is displayed to the user.

```
Promote: fn[List[PickerRegex], List[PasswordNames]] -> List[PasswordNames]
```


## Example

Consider the following ruleset:

```json
[
    {
        "^(?P<base>.*)/(user|login)$": "^{base}/pass$"
    },
    {
        "^(.*)/pass$": [
            "^{1}/(otp|OTP)$",
            "^{1}/(pin|PIN)$",
        ]
    },
    {
        "": [
            "/user$",
            "/login$",
        ]
    }
]
```

...and the following lexicographically-ordered list of password names:

```
aaaaaaaaaaaaaaaaaa
graceful.host/pass
graceful.host/user
grapefruit.home/email
grapefruit.home/pass
grapefruit.home/pin
grapefruit.home/user
horse.lan/login
horse.lan/otp
horse.lan/user
pizza.corp/user
```

### First invocation

If `pass-dmenu` is invoked without a most-recently-used password name (i.e. upon first invocation or after cancelling an invocation), the ruleset will evaluate to these *PickerRegex* expressions:

```
/user$
/login$
```

These expressions first promote everything ending in "/user", and then promote everything ending in "/login", resulting in the following final order:

```
graceful.host/user
grapefruit.home/user
horse.lan/user
pizza.corp/user
horse.lan/login
aaaaaaaaaaaaaaaaaa
graceful.host/pass
grapefruit.home/email
grapefruit.home/pass
grapefruit.home/pin
horse.lan/otp
```

Where the tersest way to select `grapefruit.home/user` would have been `pe<Right><Right><Right><Enter>` in the original order, it is now `p<Enter>`.

### Second invocation

If the user selects `grapefruit.home/user` and invokes `pass-dmenu` again, the ruleset will evaluate to these *PickerRegex* expressions:

```
^grapefruit\\.home/pass$
/user$
/login$
```

This results in the following final order:

```
grapefruit.home/pass
graceful.host/user
grapefruit.home/user
horse.lan/user
pizza.corp/user
horse.lan/login
aaaaaaaaaaaaaaaaaa
graceful.host/pass
grapefruit.home/email
grapefruit.home/pin
horse.lan/otp
```

Where the tersest way to select `grapefruit.home/pass` would have been `pe<Right><Enter>`, it is now `<Enter>`.

### Third invocation

If the user selects `grapefruit.home/pass` and invokes `pass-dmenu` again, the ruleset will evaluate to these *PickerRegex* expressions:

```
^grapefruit\\.home/(otp|OTP)$
^grapefruit\\.home/(pin|PIN)$
/user$
/login$
```

This results in the following final order:

```
grapefruit.home/pin
graceful.host/user
grapefruit.home/user
horse.lan/user
pizza.corp/user
horse.lan/login
aaaaaaaaaaaaaaaaaa
graceful.host/pass
grapefruit.home/email
grapefruit.home/pass
horse.lan/otp
```

Where the tersest way to select `grapefruit.home/pass` would have been `pe<Right><Right><Enter>`, it is now `<Enter>`.

### Fourth invocation

If the user selects `grapefruit.home/pass` and invokes `pass-dmenu` again, the ruleset will evaluate to these *PickerRegex* expressions:

```
/user$
/login$
```

And we're now back to the same order that we saw on the initial invocation.


# Environment

`PASSWORD_STORE_DIR`

: The path of the password store directory.
  Defaults to `~/.password-store`.

`PASSWORD_STORE_UMASK`

: The umask used by `pass-dmenu` when updating `.pass-dmenu.rules`.
  Defaults to 077.

`PASSWORD_STORE_DMENU`

: The path to [`dmenu`] (or equivalent).
  Defaults to `dmenu`.

`PASSWORD_STORE_X_SELECTION`

: The X selection to use for the `clip` action.
  Defaults to clipboard.  (See xclip(1) for more information.)

`PASSWORD_STORE_CLIP_TIME`

: The number of seconds the `clip` action should allot for the password to be pasted by the user before it gives up and clears the clipboard.
  Defaults to 45.


# Files

`$PASSWORD_STORE_DIR/.pass-dmenu.rules`

: The JSON ruleset for `$PASSWORD_STORE_DIR`.


`$PASSWORD_STORE_DIR/.pass-dmenu.cache`

: The password most recently selected by `pass-dmenu` for `$PASSWORD_STORE_DIR`.
  (This file will be zero-length if the most recent `pass-dmenu` invocation was cancelled without selecting a password.)


# Security considerations

This section describes the security delta between using `pass-dmenu` and using [Password Store] on its own;
it is not meant to be a comprehensive treatment.

## Cache file

Each time a password is selected (or a password selection is aborted), `$PASSWORD_STORE_DIR/.pass-dmenu.cache` will be updated atomically using `rename(2)` with the name of the most-recently-used password (or emptiness).
An adversary with read access to `$PASSWORD_STORE_DIR` could learn when you last used `pass-dmenu` by observing the change time of `.pass-dmenu.cache`, and they could learn which password you chose (or that you didn't choose a password) during that invocation by observing the contents of said file.
All of this information (and more) could also be learned by observing the access times of files in `$PASSWORD_STORE_DIR`.

By default, [Password Store] and `pass-dmenu` use a umask of 077, which prevents users other than the owner of `$PASSWORD_STORE_DIR` from observing both `.pass-dmenu.cache` and filesystem timestamps.

For additional confidentiality, `pass-dmenu` may be used with disk or file encryption schemes.

## Trusted base

`pass-dmenu` is written in Python 3, using only built-ins and the standard library.
Thus, when you trust `pass-dmenu` with your cleartext passwords, you extend the same trust to the Python 3 interpreter, to portions of the Python 3 standard library, and to their dependencies.

## Swap

In Python 3, as with most other languages in which memory management is implicit, there's no great way to keep process state from being swapped to disk during periods when memory is scarce.
As a result, cleartext passwords being handled by `pass-dmenu` could potentially wind up in a swap partition.
*This issue is not unique to this software*---it also affects [Password Store] \(which is written in bash), [`xclip`] and [`xdotool`] \(which are written in C), and many applications that consume passwords (e.g. web browsers).

The issue may be mitigated by disabling swap or by using an encrypted swap partition.

## Clipboard

`pass-dmenu clip` allows a password to be pasted no more than once before the clipboard is cleared.
This is in contrast to [Password Store], which does not clear the clipboard until `$PASSWORD_STORE_CLIP_TIME` seconds have elapsed.

[Password Store] attempts to clear password history from `klipper`, a clipboard manager.
`pass-dmenu clip` does not attempt to integrate with any clipboard managers.

`pass-dmenu type` does not interact with the clipboard.


# See also

pass(1), pass-otp(1), dmenu(1), xdotool(1), xclip(1)


# Copyright

Copyright 2019 Branen Salmon.
License GPLv3+: [GNU GPL version 3 or later](https://gnu.org/licenses/gpl.html).
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.


[Password Store]: https://www.passwordstore.org/
[`dmenu`]: https://tools.suckless.org/dmenu/
[`xdotool`]: https://www.semicomplete.com/projects/xdotool/
[`pass-otp`]: https://github.com/tadfisher/pass-otp
[`xclip`]: https://github.com/astrand/xclip
[Python regular expressions]: https://docs.python.org/3/library/re.html#regular-expression-syntax
[Python format string templates]: https://docs.python.org/3/library/string.html#formatstrings
