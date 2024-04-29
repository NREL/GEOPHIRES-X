<div class="WordSection1">

<span style="font-size:24.0pt;font-family:&quot;Trebuchet MS&quot;,sans-serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#1A1A1A;mso-font-kerning:18.0pt;mso-ligatures:none">GEOPHIRES Investment and Production Tax Credit implementation (as in the USA Inflation Reduction ACT (IRA))</span>

<span style="font-size:24.0pt;font-family:&quot;Trebuchet MS&quot;,sans-serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#1A1A1A;mso-font-kerning:18.0pt;mso-ligatures:none"></span>

<span style="font-size:19.0pt;font-family:&quot;Trebuchet MS&quot;,sans-serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#1A1A1A;mso-font-kerning:0pt;mso-ligatures:none">Introduction</span>

<span style="font-family:&quot;Palatino Linotype&quot;,serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#222222;mso-font-kerning:0pt;mso-ligatures:none">A popular method for Governments to encourage economic development is to offer tax incentives, like the Investment Tax Credit[<span class="MsoFootnoteReference"><span style="mso-special-character:footnote"><span class="MsoFootnoteReference"><span style="font-size:12.0pt;line-height:115%;
font-family:&quot;Palatino Linotype&quot;,serif;mso-fareast-font-family:&quot;Times New Roman&quot;;
mso-bidi-font-family:&quot;Times New Roman&quot;;color:#222222;mso-font-kerning:0pt;
mso-ligatures:none;mso-ansi-language:EN-US;mso-fareast-language:EN-US;
mso-bidi-language:AR-SA">[1]</span></span></span></span>](#_ftn1) (ITC) or the Production Tax Credit[<span class="MsoFootnoteReference"><span style="mso-special-character:footnote"><span class="MsoFootnoteReference"><span style="font-size:12.0pt;line-height:115%;
font-family:&quot;Palatino Linotype&quot;,serif;mso-fareast-font-family:&quot;Times New Roman&quot;;
mso-bidi-font-family:&quot;Times New Roman&quot;;color:#222222;mso-font-kerning:0pt;
mso-ligatures:none;mso-ansi-language:EN-US;mso-fareast-language:EN-US;
mso-bidi-language:AR-SA">[2]</span></span></span></span>](#_ftn2) (PTC). This type of encouragement is popular with governments because they offer a way to incentivize activities in a budget-neutral or budget-positive way � if the project is not done, the incentives are not awarded, and there is no impact on the budget; if the incentives are awarded, it is for projects that produce a taxable profit, of which the government will give up part of its tax revenue, but not all, this increasing the income of the government. They also offer new tax revenues for product purchases, new employment, and other income streams (and non-monetary benefits) that are desirable.</span>

<span style="font-family:&quot;Palatino Linotype&quot;,serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#222222;mso-font-kerning:0pt;mso-ligatures:none">An example of a PTC and ITC is in the USA Inflation Reduction Act (IRA) of 2022[<span class="MsoFootnoteReference"><span style="mso-special-character:footnote"><span class="MsoFootnoteReference"><span style="font-size:12.0pt;line-height:115%;
font-family:&quot;Palatino Linotype&quot;,serif;mso-fareast-font-family:&quot;Times New Roman&quot;;
mso-bidi-font-family:&quot;Times New Roman&quot;;color:#222222;mso-font-kerning:0pt;
mso-ligatures:none;mso-ansi-language:EN-US;mso-fareast-language:EN-US;
mso-bidi-language:AR-SA">[3]</span></span></span></span>](#_ftn3). The details of the IRA are beyond the scope of this document, but the summary is this: the IRA offers up to a 60% ITC or a 4.5 cent/kWh PTC. In the case of an ITC, a �60% ITC� means that up to 60% of the investment in a project be written down against the investor's tax liability for the year the ITC was awarded. If the entity receiving the ITC award is a non-taxable entity, the tax liability write-off can be sold in <span class="GramE">an exchange</span> to any company that has a liability. In the case of a PTC, the US government will award a tax write-off equivalent to 4.5 cents/kWh of electricity produced.</span>

<span style="font-family:&quot;Palatino Linotype&quot;,serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#222222;mso-font-kerning:0pt;mso-ligatures:none">This document explains how the ITC and PTC are incorporated in GEOPHIRES-X. It is implemented in a generic way that works for any ITC and/or PTC for which the project qualifies (IRA or otherwise)�the examples herein will use the IRA for illustrative purposes. Note that PTCs and/or ITCs may be cumulative � an award of a PTC from the federal level may be added to a state-level PTC, for example. In that case, sum the PTCs and/or ITCs values when you use them in GEOPHIRES-X. Also note that the IRA offer only an ITC <u>OR</u> a PTC, not both.</span>

<span style="font-family:&quot;Palatino Linotype&quot;,serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#222222;mso-font-kerning:0pt;mso-ligatures:none"></span>

<span style="font-family:&quot;Palatino Linotype&quot;,serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#222222;mso-font-kerning:0pt;mso-ligatures:none"><span style="mso-spacerun:yes">�</span></span><span style="font-size:19.0pt;
font-family:&quot;Trebuchet MS&quot;,sans-serif;mso-fareast-font-family:&quot;Times New Roman&quot;;
mso-bidi-font-family:&quot;Times New Roman&quot;;color:#1A1A1A;mso-font-kerning:0pt;
mso-ligatures:none">Implementing an ITC in GEOPHIRES</span>

<span style="font-family:&quot;Palatino Linotype&quot;,serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#222222;mso-font-kerning:0pt;mso-ligatures:none">An ITC is implemented in GEOPHIRES-X through the BICYCLE Economic model. It will not be calculated for any other economic model. One additional parameter is added:</span>

<div style="mso-element:para-border-div;border:solid #DDDDDD 1.0pt;mso-border-alt:
solid #DDDDDD .75pt;padding:4.0pt 4.0pt 4.0pt 4.0pt;background:#FFFDFD">

<span style="font-size:11.5pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none">Investment Tax Credit Rate,0.5, --- [-] Investment tax credit rate</span>

</div>

<span style="font-family:&quot;Palatino Linotype&quot;,serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#222222;mso-font-kerning:0pt;mso-ligatures:none">In this case, the ITC is set to 50%. It could represent an ITC from the IRA or the sum of several ITCs from several taxation entities.</span>

<span style="font-family:&quot;Palatino Linotype&quot;,serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#222222;mso-font-kerning:0pt;mso-ligatures:none">After GEOPHIRES makes its Capital Expenditure[<span class="MsoFootnoteReference"><span style="mso-special-character:footnote"><span class="MsoFootnoteReference"><span style="font-size:12.0pt;line-height:115%;
font-family:&quot;Palatino Linotype&quot;,serif;mso-fareast-font-family:&quot;Times New Roman&quot;;
mso-bidi-font-family:&quot;Times New Roman&quot;;color:#222222;mso-font-kerning:0pt;
mso-ligatures:none;mso-ansi-language:EN-US;mso-fareast-language:EN-US;
mso-bidi-language:AR-SA">[4]</span></span></span></span>](#_ftn4) (CAPEX) calculations, it will subtract the value of the ITC credit from CAPEX and will report it as follows:</span>

<div style="mso-element:para-border-div;border:solid #DDDDDD 1.0pt;mso-border-alt:
solid #DDDDDD .75pt;padding:4.0pt 4.0pt 4.0pt 4.0pt;background:#FFFDFD">

**<span style="font-size:11.5pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none">***CAPITAL COSTS (M<span class="GramE">$)*</span>**</span>**

**<span style="font-size:11.5pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none"></span>**

**<span style="font-size:11.5pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none"><span style="mso-spacerun:yes"></span> Drilling and completion costs:<span style="mso-spacerun:yes"></span> 21.95 MUSD</span>**

**<span style="font-size:11.5pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none"><span style="mso-spacerun:yes"></span> Drilling and completion costs per well:<span style="mso-spacerun:yes"></span> 5.49 MUSD</span>**

**<span style="font-size:11.5pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none"><span style="mso-spacerun:yes"></span> Stimulation costs:<span style="mso-spacerun:yes"></span> 0.00 MUSD</span>**

**<span style="font-size:11.5pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none"><span style="mso-spacerun:yes"></span> Surface power plant costs:<span style="mso-spacerun:yes"></span> 20.78 MUSD</span>**

**<span style="font-size:11.5pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none"><span style="mso-spacerun:yes"></span> Field gathering system costs:<span style="mso-spacerun:yes"></span> 2.32 <span class="GramE">MUSD</span></span>**

**<span style="font-size:11.5pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none"><span style="mso-spacerun:yes"></span> Total surface equipment costs:<span style="mso-spacerun:yes"></span> 23.10 MUSD</span>**

**<span style="font-size:11.5pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none"><span style="mso-spacerun:yes"></span> Exploration costs:<span style="mso-spacerun:yes"></span> 5.33 MUSD</span>**

**<span style="font-size:11.5pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none"><span style="mso-spacerun:yes"></span> <span style="background:yellow;
mso-highlight:yellow">Investment Tax Credit:<span style="mso-spacerun:yes"></span> -25.18 MUSD</span></span>**

**<span style="font-size:11.5pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none"><span style="mso-spacerun:yes"></span> Total capital costs:<span style="mso-spacerun:yes"></span> 25.18 MUSD</span>**<span style="font-size:11.5pt;font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;
mso-bidi-font-family:&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;
mso-ligatures:none"></span>

</div>

<span style="font-family:&quot;Palatino Linotype&quot;,serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#222222;mso-font-kerning:0pt;mso-ligatures:none">Note that the ITC and the total capital costs are equal because the ITC is 50% of the total capital cost. Without the ITC, the project CAPEX was 50.36 MMUSD.</span>

<span style="font-family:&quot;Palatino Linotype&quot;,serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#222222;mso-font-kerning:0pt;mso-ligatures:none">Reducing the CAPEX has many other economic modeling impacts. For example:</span>

<div style="mso-element:para-border-div;border:solid #DDDDDD 1.0pt;mso-border-alt:
solid #DDDDDD .75pt;padding:4.0pt 4.0pt 4.0pt 4.0pt;background:#FFFDFD">

<span style="font-size:11.5pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none">Electricity breakeven price: 5.31 cents/kWh (without ITC: 13.24 cents/kWh)</span>

<span style="font-size:11.5pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none">Project NPV:<span style="mso-spacerun:yes"></span> <span style="mso-spacerun:yes">���</span>-12.81 MUSD (without ITC: -37.99 MUSD)</span>

<span style="font-size:11.5pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none">Project IRR:<span style="mso-spacerun:yes"></span> <span style="mso-spacerun:yes">����</span>0.61% (without ITC: -3.53%)</span>

<span style="font-size:11.5pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none">Project VIR=PI=PIR:<span style="mso-spacerun:yes"></span> <span style="mso-spacerun:yes">���</span><span class="GramE">0.49<span style="mso-spacerun:yes"></span> (</span>without ITC: 0.25)</span>

<span style="font-size:11.5pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none">Project MOIC:<span style="mso-spacerun:yes"></span> <span style="mso-spacerun:yes">���</span><span class="GramE">0.04<span style="mso-spacerun:yes"></span> (</span>without ITC: -0.25)</span>

<span style="font-size:11.5pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none">Project Payback Period: <span style="mso-spacerun:yes">�</span>28.00 <span class="SpellE"><span class="GramE">yrs</span></span><span class="GramE"><span style="mso-spacerun:yes"></span> (</span>without ITC: never)</span>

</div>

<span style="font-family:&quot;Palatino Linotype&quot;,serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#222222;mso-font-kerning:0pt;mso-ligatures:none"></span>

<span style="font-family:&quot;Palatino Linotype&quot;,serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#222222;mso-font-kerning:0pt;mso-ligatures:none"><span style="mso-spacerun:yes">�</span></span><span style="font-size:19.0pt;
font-family:&quot;Trebuchet MS&quot;,sans-serif;mso-fareast-font-family:&quot;Times New Roman&quot;;
mso-bidi-font-family:&quot;Times New Roman&quot;;color:#1A1A1A;mso-font-kerning:0pt;
mso-ligatures:none">Implementing a PTC in GEOPHIRES</span>

<span style="font-family:&quot;Palatino Linotype&quot;,serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#222222;mso-font-kerning:0pt;mso-ligatures:none">A PTC is also implemented in GEOPHIRES-X through only the BICYCLE Economic model. Several additional parameters have been added:</span>

<div style="mso-element:para-border-div;border:solid #DDDDDD 1.0pt;mso-border-alt:
solid #DDDDDD .75pt;padding:4.0pt 4.0pt 4.0pt 4.0pt;background:#FFFDFD">

<span style="font-size:11.5pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none">Production Tax Credit Electricity, 0.05, ---$/kWh</span>

<span style="font-size:11.5pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none">Production Tax Credit Heat, 0.05,<span style="mso-spacerun:yes"></span> ---$/kWh</span>

<span style="font-size:11.5pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none">Production Tax Credit Cooling, 0.05,<span style="mso-spacerun:yes"></span> ---$/kWh</span>

<span style="font-size:11.5pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none">Production Tax Credit Duration, <span class="GramE">10,<span style="mso-spacerun:yes"></span> </span><span style="mso-spacerun:yes">���</span>---in years</span>

<span style="font-size:11.5pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none">Production Tax Credit Inflation Adjusted, <span class="GramE">True,<span style="mso-spacerun:yes"></span> ---</span> (T/F)</span>

</div>

<span style="font-family:&quot;Palatino Linotype&quot;,serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#222222;mso-font-kerning:0pt;mso-ligatures:none">PTC differs from ITC in that it can be applied differently (or not at all) to different products (electricity vs. heat vs. cooling). In the case of the ITC, the PTC applies only to electricity � no incentives for heating or cooling. This example grants 5 cents/kWh for electricity (and the same for heating and cooling, but the model that is running for electricity only, so the only thing that gets the PTC is the electricity output). In the case of the PTC, the <span class="GramE">time period</span> is limited to 10 years from the time of the start of the project, so GEOPHIRES-X implements a parameter to control that duration (�</span><span style="font-size:11.5pt;font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;
mso-bidi-font-family:&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;
mso-ligatures:none">Production Tax Credit Duration</span><span style="font-family:&quot;Palatino Linotype&quot;,serif;mso-fareast-font-family:&quot;Times New Roman&quot;;
mso-bidi-font-family:&quot;Times New Roman&quot;;color:#222222;mso-font-kerning:0pt;
mso-ligatures:none">�). Another feature of the PTC in the IRA is that the PTC amount can be indexed to inflation, controlled by the Boolean parameter �</span><span style="font-size:11.5pt;font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;
mso-bidi-font-family:&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;
mso-ligatures:none">Production Tax Credit Inflation Adjusted</span><span style="font-family:&quot;Palatino Linotype&quot;,serif;mso-fareast-font-family:&quot;Times New Roman&quot;;
mso-bidi-font-family:&quot;Times New Roman&quot;;color:#222222;mso-font-kerning:0pt;
mso-ligatures:none">�).</span>

<span style="font-family:&quot;Palatino Linotype&quot;,serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#222222;mso-font-kerning:0pt;mso-ligatures:none">GEOPHIRES-X accounts for the value of the PTC by automatically adding it to the annual electricity price for the duration of the PTC. In the output, that looks like this (note that the base price for electricity in this example is 5.5 cents/kWh):</span>

<div style="mso-element:para-border-div;border:solid #DDDDDD 1.0pt;mso-border-alt:
solid #DDDDDD .75pt;padding:4.0pt 4.0pt 4.0pt 4.0pt;background:#FFFDFD">

<span style="font-size:7.0pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none">Year<span style="mso-spacerun:yes"></span> Electricity<span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> Heat<span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> Cooling<span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> Carbon<span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> Project</span>

<span style="font-size:7.0pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none">Since<span style="mso-spacerun:yes"></span> Price<span style="mso-spacerun:yes"></span> Ann. Rev.<span style="mso-spacerun:yes"></span> Cumm. Rev. |<span style="mso-spacerun:yes"></span> Price<span style="mso-spacerun:yes"></span> Ann. Rev.<span style="mso-spacerun:yes"></span> Cumm. Rev. <span class="GramE">|<span style="mso-spacerun:yes"></span> Price</span><span style="mso-spacerun:yes"></span> Ann. Rev.<span style="mso-spacerun:yes"></span> Cumm. Rev.<span style="mso-spacerun:yes">��</span></span>

<span style="font-size:7.0pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none">Start <span class="GramE"><span style="mso-spacerun:yes">���</span>(</span>cents/kWh)(MUSD/<span class="SpellE">yr</span>) (MUSD)<span style="mso-spacerun:yes"></span> |(cents/kWh) (MUSD/<span class="SpellE">yr</span>)<span style="mso-spacerun:yes"></span> (MUSD)<span style="mso-spacerun:yes"></span> |(cents/kWh) (MUSD/<span class="SpellE">yr</span>)<span style="mso-spacerun:yes"></span> (MUSD)</span>

<span style="font-size:7.0pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none">________________________________________________________________________________________________________________________</span>

<span style="font-size:7.0pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none"><span style="mso-spacerun:yes"></span> 1<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> -50.37<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> 0.00</span>

<span style="font-size:7.0pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none"><span style="mso-spacerun:yes"></span> 2<span style="mso-spacerun:yes"></span> <span style="background:yellow;mso-highlight:yellow">10.50<span style="mso-spacerun:yes"></span> 2.95<span style="mso-spacerun:yes"></span> 4.35</span><span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> 7.50<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> 7.50<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> 0.00</span>

<span style="font-size:7.0pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none"><span style="mso-spacerun:yes"></span> 3<span style="mso-spacerun:yes"></span> <span style="background:yellow;mso-highlight:yellow">10.62<span style="mso-spacerun:yes"></span> 3.05<span style="mso-spacerun:yes"></span> 8.79</span><span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> 7.62<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> 7.62<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> 0.00</span>

<span style="font-size:7.0pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none"><span style="mso-spacerun:yes"></span> 4<span style="mso-spacerun:yes"></span> <span style="background:yellow;mso-highlight:yellow">10.75<span style="mso-spacerun:yes"></span> <span class="GramE">3.12<span style="mso-spacerun:yes"></span> 13.31</span></span><span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> 7.75<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> 7.75<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> 0.00</span>

<span style="font-size:7.0pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none"><span style="mso-spacerun:yes"></span> 5<span style="mso-spacerun:yes"></span> <span style="background:yellow;mso-highlight:yellow">10.88<span style="mso-spacerun:yes"></span> <span class="GramE">3.19<span style="mso-spacerun:yes"></span> 17.89</span></span><span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> 7.88<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> 7.88<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> 0.00</span>

<span style="font-size:7.0pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none"><span style="mso-spacerun:yes"></span> 6<span style="mso-spacerun:yes"></span> <span style="background:yellow;mso-highlight:yellow">11.02<span style="mso-spacerun:yes"></span> <span class="GramE">3.25<span style="mso-spacerun:yes"></span> 22.54</span></span><span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> 8.02<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> 8.02<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> 0.00</span>

<span style="font-size:7.0pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none"><span style="mso-spacerun:yes"></span> 7<span style="mso-spacerun:yes"></span> <span style="background:yellow;mso-highlight:yellow">11.16<span style="mso-spacerun:yes"></span> <span class="GramE">3.31<span style="mso-spacerun:yes"></span> 27.25</span></span><span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> 8.16<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> 8.16<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> 0.00</span>

<span style="font-size:7.0pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none"><span style="mso-spacerun:yes"></span> 8<span style="mso-spacerun:yes"></span> <span style="background:yellow;mso-highlight:yellow">11.30<span style="mso-spacerun:yes"></span> <span class="GramE">3.38<span style="mso-spacerun:yes"></span> 32.02</span></span><span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> 8.30<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> 8.30<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> 0.00</span>

<span style="font-size:7.0pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none"><span style="mso-spacerun:yes"></span> 9<span style="mso-spacerun:yes"></span> <span style="background:yellow;mso-highlight:yellow">11.44<span style="mso-spacerun:yes"></span> <span class="GramE">3.44<span style="mso-spacerun:yes"></span> 36.86</span></span><span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> 8.44<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> 8.44<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> 0.00</span>

<span style="font-size:7.0pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none"><span style="mso-spacerun:yes">�</span>10<span style="mso-spacerun:yes"></span> <span style="background:yellow;mso-highlight:yellow">11.59<span style="mso-spacerun:yes"></span> <span class="GramE">3.51<span style="mso-spacerun:yes"></span> 41.77</span></span><span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> 8.59<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> 8.59<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> 0.00</span>

<span style="font-size:7.0pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none"><span style="mso-spacerun:yes">�</span>11<span style="mso-spacerun:yes"></span> <span style="background:yellow;mso-highlight:yellow">11.74<span style="mso-spacerun:yes"></span> <span class="GramE">3.58<span style="mso-spacerun:yes"></span> 46.74</span></span><span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> 8.74<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> 8.74<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> 0.00</span>

<span style="font-size:7.0pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none"><span style="mso-spacerun:yes">�</span>12<span style="mso-spacerun:yes"></span> 5.50<span style="mso-spacerun:yes"></span> <span class="GramE">0.93<span style="mso-spacerun:yes"></span> 49.07</span><span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> 2.50<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> 2.50<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> 0.00</span>

<span style="font-size:7.0pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none"><span style="mso-spacerun:yes">�</span>13<span style="mso-spacerun:yes"></span> 5.50<span style="mso-spacerun:yes"></span> <span class="GramE">0.94<span style="mso-spacerun:yes"></span> 51.40</span><span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> 2.50<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> |<span style="mso-spacerun:yes"></span> 2.50<span style="mso-spacerun:yes"></span> 0.00<span style="mso-spacerun:yes"></span> 0.00</span>

</div>

In this case, Year 1 is a construction year; Year 2 is the first year of the PTC (so the price is 5.5 cents (base price) plus 5 cents (PTC ); and the subsidy rises by the inflation specified in the BICYCLE model (in this case, 2%) for 10 years (through year 11) when the subsidy terminates, and the price goes back to 5.5 cents/kWh.

<span style="font-family:&quot;Palatino Linotype&quot;,serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#222222;mso-font-kerning:0pt;mso-ligatures:none">Increasing the effective electricity price by the PTC has many other economic modeling impacts. For example:</span>

<div style="mso-element:para-border-div;border:solid #DDDDDD 1.0pt;mso-border-alt:
solid #DDDDDD .75pt;padding:4.0pt 4.0pt 4.0pt 4.0pt;background:#FFFDFD">

<span style="font-size:11.5pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none">Project NPV:<span style="mso-spacerun:yes"></span> -21.06 MUSD (without ITC: -37.99 MUSD, ITC: -12.81 MUSD)</span>

<span style="font-size:11.5pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none">Project IRR:<span style="mso-spacerun:yes"></span> <span style="mso-spacerun:yes">����</span>0.15% (without ITC: -3.53%, ITC: 0.61%)</span>

<span style="font-size:11.5pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none">Project VIR=PI=PIR:<span style="mso-spacerun:yes"></span> <span style="mso-spacerun:yes">���</span><span class="GramE">0.58<span style="mso-spacerun:yes"></span> (</span>without ITC: 0.25, ITC: 0.49)</span>

<span style="font-size:11.5pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none">Project MOIC:<span style="mso-spacerun:yes"></span> <span style="mso-spacerun:yes">���</span><span class="GramE">0.01<span style="mso-spacerun:yes"></span> (</span>without ITC: -0.25, ITC: 0.04)</span>

<span style="font-size:11.5pt;
font-family:Consolas;mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:
&quot;Courier New&quot;;color:#222222;mso-font-kerning:0pt;mso-ligatures:none">Project Payback Period: <span style="mso-spacerun:yes">�</span>29.69 <span class="SpellE"><span class="GramE">yrs</span></span><span class="GramE"><span style="mso-spacerun:yes"></span> (</span>without ITC: never, ITC: 28 years)</span>

</div>

<span style="font-family:&quot;Palatino Linotype&quot;,serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#222222;mso-font-kerning:0pt;mso-ligatures:none">The conclusion that can be drawn from this is that for this scenario, accepting the 50% ITC will produce a slightly better financial result than accepting a 5 cent/kWh (inflation-adjusted) PTC. Different scenarios will yield different results.</span>

<span style="font-family:&quot;Palatino Linotype&quot;,serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#222222;mso-font-kerning:0pt;mso-ligatures:none">Visualized graphically, the price and cash flow over the life of the project:</span>

<span style="font-family:&quot;Palatino Linotype&quot;,serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#222222;mso-font-kerning:0pt;mso-no-proof:yes">![](PTCandITCinGEOPHIRES_files/image002.png)</span><span style="font-family:&quot;Palatino Linotype&quot;,serif;mso-fareast-font-family:&quot;Times New Roman&quot;;
mso-bidi-font-family:&quot;Times New Roman&quot;;color:#222222;mso-font-kerning:0pt;
mso-ligatures:none"></span>

<span style="font-size:19.0pt;font-family:&quot;Trebuchet MS&quot;,sans-serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#1A1A1A;mso-font-kerning:0pt;mso-ligatures:none">Example</span><span style="color:black;mso-color-alt:windowtext">[<span style="font-size:15.0pt;font-family:&quot;Trebuchet MS&quot;,sans-serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#00608F;mso-font-kerning:0pt;mso-ligatures:none">�</span>](https://nrel.github.io/GEOPHIRES-X/Monte-Carlo-User-Guide.html#documentation "Link to this heading")</span><span style="font-size:19.0pt;font-family:&quot;Trebuchet MS&quot;,sans-serif;mso-fareast-font-family:
&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;color:#1A1A1A;
mso-font-kerning:0pt;mso-ligatures:none"></span>

<span style="font-family:&quot;Palatino Linotype&quot;,serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#222222;mso-font-kerning:0pt;mso-ligatures:none">See�Example1_ITC.txt</span>

<span style="font-size:19.0pt;font-family:&quot;Trebuchet MS&quot;,sans-serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#1A1A1A;mso-font-kerning:0pt;mso-ligatures:none">Related Parameters</span><span style="color:black;mso-color-alt:windowtext">[<span style="font-size:15.0pt;font-family:&quot;Trebuchet MS&quot;,sans-serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#00608F;mso-font-kerning:0pt;mso-ligatures:none">�</span>](https://nrel.github.io/GEOPHIRES-X/Monte-Carlo-User-Guide.html#documentation "Link to this heading")</span><span style="font-size:19.0pt;font-family:&quot;Trebuchet MS&quot;,sans-serif;mso-fareast-font-family:
&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;color:#1A1A1A;
mso-font-kerning:0pt;mso-ligatures:none"></span>

<span style="font-family:&quot;Palatino Linotype&quot;,serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#222222;mso-font-kerning:0pt;mso-ligatures:none">"Tax Relief Per Year:" All Models: <span class="GramE">Similar to</span> ITC, this is a Constant Dollar Value that is subtracted from the Operating Expenditure. It is not indexed to inflation and applies for the duration of the project.<span style="mso-spacerun:yes">�</span></span>

<span style="font-family:&quot;Palatino Linotype&quot;,serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#222222;mso-font-kerning:0pt;mso-ligatures:none">�Combined Income Tax Rate:� BICYCLE Model: Combined income tax rate. Income taxes in each year are calculated using (combined income tax rate) � (revenue � deductible expenses) � investment tax credits.</span>

<span style="font-family:&quot;Palatino Linotype&quot;,serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#222222;mso-font-kerning:0pt;mso-ligatures:none">�Gross Revenue Tax Rate:� BICYCLE Model: Gross revenue tax rate. Gross revenue taxes in each year are calculated using (gross revenue tax rate) � (revenue).</span>

<span style="font-family:&quot;Palatino Linotype&quot;,serif;
mso-fareast-font-family:&quot;Times New Roman&quot;;mso-bidi-font-family:&quot;Times New Roman&quot;;
color:#222222;mso-font-kerning:0pt;mso-ligatures:none">�Property Tax Rate:� BICYCLE Model: Property tax rate. Property taxes are fixed annual charges and are calculated using (property tax rate) � (initial capital investment).</span>

</div>

<div style="mso-element:footnote-list">

* * *

<div style="mso-element:footnote" id="ftn1">

[<span class="MsoFootnoteReference"><span style="mso-special-character:
footnote"><span class="MsoFootnoteReference"><span style="font-size:10.0pt;line-height:115%;font-family:&quot;Aptos&quot;,sans-serif;
mso-ascii-theme-font:minor-latin;mso-fareast-font-family:Aptos;mso-fareast-theme-font:
minor-latin;mso-hansi-theme-font:minor-latin;mso-bidi-font-family:&quot;Times New Roman&quot;;
mso-bidi-theme-font:minor-bidi;mso-ansi-language:EN-US;mso-fareast-language:
EN-US;mso-bidi-language:AR-SA">[1]</span></span></span></span>](#_ftnref1) https://content.next.westlaw.com/practical-law/document/I03f4d8caeee311e28578f7ccc38dcbee/Investment-Tax-Credit-ITC

</div>

<div style="mso-element:footnote" id="ftn2">

[<span class="MsoFootnoteReference"><span style="mso-special-character:
footnote"><span class="MsoFootnoteReference"><span style="font-size:10.0pt;line-height:115%;font-family:&quot;Aptos&quot;,sans-serif;
mso-ascii-theme-font:minor-latin;mso-fareast-font-family:Aptos;mso-fareast-theme-font:
minor-latin;mso-hansi-theme-font:minor-latin;mso-bidi-font-family:&quot;Times New Roman&quot;;
mso-bidi-theme-font:minor-bidi;mso-ansi-language:EN-US;mso-fareast-language:
EN-US;mso-bidi-language:AR-SA">[2]</span></span></span></span>](#_ftnref2) https://content.next.westlaw.com/practical-law/document/I03f4d8cceee311e28578f7ccc38dcbee/Production-Tax-Credit-PTC

</div>

<div style="mso-element:footnote" id="ftn3">

[<span class="MsoFootnoteReference"><span style="mso-special-character:
footnote"><span class="MsoFootnoteReference"><span style="font-size:10.0pt;line-height:115%;font-family:&quot;Aptos&quot;,sans-serif;
mso-ascii-theme-font:minor-latin;mso-fareast-font-family:Aptos;mso-fareast-theme-font:
minor-latin;mso-hansi-theme-font:minor-latin;mso-bidi-font-family:&quot;Times New Roman&quot;;
mso-bidi-theme-font:minor-bidi;mso-ansi-language:EN-US;mso-fareast-language:
EN-US;mso-bidi-language:AR-SA">[3]</span></span></span></span>](#_ftnref3) https://vitalsigns.edf.org/story/inflation-reduction-act-victory-climate-heres-what-comes-next

</div>

<div style="mso-element:footnote" id="ftn4">

[<span class="MsoFootnoteReference"><span style="mso-special-character:
footnote"><span class="MsoFootnoteReference"><span style="font-size:10.0pt;line-height:115%;font-family:&quot;Aptos&quot;,sans-serif;
mso-ascii-theme-font:minor-latin;mso-fareast-font-family:Aptos;mso-fareast-theme-font:
minor-latin;mso-hansi-theme-font:minor-latin;mso-bidi-font-family:&quot;Times New Roman&quot;;
mso-bidi-theme-font:minor-bidi;mso-ansi-language:EN-US;mso-fareast-language:
EN-US;mso-bidi-language:AR-SA">[4]</span></span></span></span>](#_ftnref4) https://www.investopedia.com/terms/c/capitalexpenditure.asp

</div>

</div>
