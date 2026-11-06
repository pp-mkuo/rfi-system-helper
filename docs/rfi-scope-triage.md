# RFI scope triage — what CS answers, what routes out

Reference for Client Strategy team members working an RFI questionnaire. Encoded in the `rfi-system-helper` skill.

## The test

> **What the platform DOES → CS answers.**
> **How the company HANDLES a topic → Internet Brands RFI team.**

RFI only. If a request turns into line items, impression math, flight dates, or a priced media plan, that's the RFP process (`rfp-builder` skill). Explaining *how pricing models work* is an RFI answer; *quoting a campaign* is not.

## 🟢 GREEN — CS scope

General overview of PulsePoint capabilities for programmatic activations:

- Targeting
- Reporting
- Pricing — models and structures, not a quote
- Methodologies
- PulsePoint-specific teams (product, marketing, supply/exchange, brand safety, etc.)

## 🟡 AMBER — CS owns it, needs an internal SME

Still a PulsePoint capability question, but past what the Loopio library covers — unreleased roadmap, exchange/supply-path specifics, unusual technical integrations. CS keeps the question and contacts the relevant internal team.

## 🔴 RED — Internet Brands RFI team

An in-depth review of policies or procedures — how the company handles a topic rather than what the platform does:

- HR policies
- Sustainability and DE&I
- Data/platform security
- Legal
- Anything sourced from IB teams (legal, security, etc.)

**Red questions are never drafted.** No searching, no assembling from adjacent records, no "starting point." The library holds capability language that can look responsive to a security or legal question, and using it that way is the specific risk this rule prevents.

## Where the line actually falls

| Question | Call |
|---|---|
| Is your data HIPAA-compliant and de-identified to regulatory standards? | 🟢 platform methodology — library has vetted language |
| Can you target by medical condition and remain HIPAA compliant? | 🟢 targeting capability |
| Provide your information security policy / SOC 2 / pen test results | 🔴 company procedure |
| Describe your incident response process | 🔴 company procedure |
| What is your data retention policy? / Do you have a DPA? | 🔴 legal/policy |
| Which brand safety vendors do you integrate with? | 🟢 platform capability |
| What is your content moderation policy? | 🔴 company policy |
| What does your product team own? | 🟢 PulsePoint teams |
| What is your DE&I hiring commitment? | 🔴 IB RFI team |

A question that straddles the line gets split: capability half green, policy half red.

## Export requirement

The triaged workbook must **open** with the scope summary — how many questions are outside CS scope, how many go to the IB RFI team (listed by number), how many need an internal SME, and how many CS answered with flags outstanding. The first thing anyone wants to know is what they have to chase down; that never gets buried at the bottom.
