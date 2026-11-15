$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$root=Split-Path -Parent $PSScriptRoot
$d=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'content.json') -Raw -Encoding UTF8|ConvertFrom-Json
$navy='#0B2148';$paper='#F5F1E9';$ink='#172C42';$muted='#61717A';$rust='#BE6346';$pale='#E0D7CA';$teal='#2F706D';$white='#FFFFFF'
$script:fonts=@{};$script:audit=[System.Collections.Generic.List[object]]::new()
function C($s){[System.Drawing.ColorTranslator]::FromHtml($s)}
function F([float]$size,[bool]$bold=$false,[string]$family='Microsoft YaHei'){
 $k="$size/$bold/$family"
 if(!$script:fonts.ContainsKey($k)){$st=[System.Drawing.FontStyle]::Regular;if($bold){$st=[System.Drawing.FontStyle]::Bold};$script:fonts[$k]=[System.Drawing.Font]::new($family,$size,$st,[System.Drawing.GraphicsUnit]::Pixel)}
 return $script:fonts[$k]
}
function Rect([float]$x,[float]$y,[float]$w,[float]$h,$co){
 $b=[System.Drawing.SolidBrush]::new((C $co));$script:g.FillRectangle($b,$x,$y,$w,$h);$b.Dispose()
}
function Line([float]$x,[float]$y,[float]$xx,[float]$yy,$co,[float]$th=2){
 $p=[System.Drawing.Pen]::new((C $co),$th);$script:g.DrawLine($p,$x,$y,$xx,$yy);$p.Dispose()
}
function Dot([float]$x,[float]$y,[float]$w,$co){
 $b=[System.Drawing.SolidBrush]::new((C $co));$script:g.FillEllipse($b,$x,$y,$w,$w);$b.Dispose()
}
function Wrap([string]$txt,[float]$sz,[float]$w,[bool]$bold=$false,[string]$family='Microsoft YaHei'){
 $font=F $sz $bold $family;$ls=[System.Collections.Generic.List[string]]::new()
 foreach($para in ($txt -split "\r?\n")){
  if($para.Length-eq 0){$ls.Add('');continue};$s=''
  foreach($ch in $para.ToCharArray()){
   $trial=$s+$ch;$m=$script:g.MeasureString($trial,$font,[System.Drawing.PointF]::new(0,0),[System.Drawing.StringFormat]::GenericTypographic)
   if($s.Length-gt 0-and$m.Width-gt$w){
    if($s.Length-gt 1-and('，。；：？！、）》.'.Contains([string]$ch)-or'（《'.Contains([string]$s[$s.Length-1]))){
     $tail=$s.Substring($s.Length-1);$ls.Add($s.Substring(0,$s.Length-1));$s=$tail+$ch
    }else{$ls.Add($s);$s=[string]$ch}
   }else{$s=$trial}
  }
  if($s.Length-gt 0){$ls.Add($s)}
 }
 return ,$ls.ToArray()
}
function MeasureContent([string]$txt,[float]$sz,[float]$w,[float]$lh,[bool]$bold=$false){$ls=Wrap $txt $sz $w $bold;return [float]($ls.Count*$lh)}
function T([string]$txt,[float]$x,[float]$y,[float]$sz,$co=$ink,[float]$w=920,[float]$lh=0,[bool]$bold=$false,[string]$family='Microsoft YaHei'){
 if($lh-eq 0){$lh=$sz*1.56};$ls=Wrap $txt $sz $w $bold $family
 $font=F $sz $bold $family;$b=[System.Drawing.SolidBrush]::new((C $co));$yy=$y
 foreach($s in $ls){$script:g.DrawString($s,$font,$b,[System.Drawing.PointF]::new($x,$yy),[System.Drawing.StringFormat]::GenericTypographic);$yy+=$lh}
 $b.Dispose();$script:audit.Add(@{page=$script:pg;text=$txt;x=$x;y=$y;width=$w;size=$sz;lines=$ls.Count;height=($yy-$y)})
 return [float]($yy-$y)
}
function Canvas($pg){
 $script:pg=$pg;$script:bmp=[System.Drawing.Bitmap]::new(1080,9000,[System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
 $script:bmp.SetResolution(144,144);$script:g=[System.Drawing.Graphics]::FromImage($script:bmp)
 $script:g.SmoothingMode=[System.Drawing.Drawing2D.SmoothingMode]::AntiAlias;$script:g.TextRenderingHint=[System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
 $script:g.Clear((C $paper))
}
function Brand($co=$navy){
 [void](T '格拉斯哥大学北京校友会' 80 62 32 $co 920 52 $true)
 [void](T 'UNIVERSITY OF GLASGOW  /  BEIJING ALUMNI' 80 119 22 $co 920 38 $false 'Georgia')
}
function Label($txt,$y){[void](T $txt 80 $y 30 $rust 920 46 $true)}
function Save($y,$name){
 Line 80 ($y+12) 1000 ($y+12) $pale 2
 [void](T '格拉斯哥大学北京校友会' 80 ($y+44) 31 $navy 810 50 $true)
 [void](T ('0'+$script:pg+' / 03') 895 ($y+50) 25 $muted 160 40 $false 'Georgia')
 $height=[int][Math]::Ceiling($y+155);if($height-gt 8900){throw '画布过长'}
 $crop=$script:bmp.Clone([System.Drawing.Rectangle]::new(0,0,1080,$height),[System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
 $path=Join-Path (Join-Path $root 'images') $name;$crop.Save($path,[System.Drawing.Imaging.ImageFormat]::Png)
 $crop.Dispose();$script:g.Dispose();$script:bmp.Dispose()
 return [PSCustomObject]@{file=$name;width=1080;height=$height;bytes=(Get-Item -LiteralPath $path).Length}
}
function Skyline{
 $co='#204468';$pts=@(@(724,1120),@(724,995),@(765,995),@(765,936),@(792,936),@(792,904),@(811,904),@(811,936),@(835,936),@(835,995),@(861,995),@(861,878),@(879,878),@(879,845),@(891,845),@(891,796),@(908,758),@(924,796),@(924,845),@(937,845),@(937,878),@(954,878),@(954,995),@(983,995),@(983,931),@(1001,931),@(1001,909),@(1019,909),@(1019,931),@(1042,931),@(1042,1120))
 for($i=0;$i-lt$pts.Count-1;$i++){Line $pts[$i][0] $pts[$i][1] $pts[$i+1][0] $pts[$i+1][1] $co 3}
 foreach($xx in @(789,812,882,907,931,997,1020)){foreach($yy in @(1008,1053)){Rect $xx $yy 8 22 $co}}
}
$r=[System.Collections.Generic.List[object]]::new()
Canvas 1
Rect 0 0 1080 1140 $navy
Brand '#F5F1E9';Line 80 191 1000 191 '#38506E'
Rect 80 241 243 63 $rust
[void](T '活动预告' 111 251 32 $white 195 48 $true)
[void](T '就业指导' 72 363 116 $white 960 154 $true)
[void](T '沙龙' 72 510 116 $white 960 154 $true)
[void](T '从校园到职场，下一步怎么走？' 80 712 47 '#D7E3E5' 920 73)
[void](T ("银行 · 证券 · 股权投资"+[Environment]::NewLine+"互联网 · 硬科技 · 财富管理") 80 829 39 '#D7E3E5' 920 63)
Skyline
[void](T $d.hero_date 80 1007 62 $white 650 91 $true)
[void](T $d.hero_time 80 1091 29 '#C7D6DE' 670 44)
$y=1242;Label '01  /  为什么相聚' $y;$y+=85
$y+=(T ("把求职里的疑问，"+[Environment]::NewLine+"交给走过这段路的校友。") 80 $y 60 $navy 920 88 $true);$y+=45
foreach($p in $d.intro){$y+=(T $p 80 $y 44 $ink 920 73);$y+=27}
$y+=55;Label '三个主题，聊得具体一点' $y;$y+=91;$i=1
foreach($p in $d.pillars){
 Line 80 ($y-12) 1000 ($y-12) $pale
 [void](T ('0'+$i) 80 ($y+20) 57 $rust 112 82 $false 'Georgia')
 $h=(T $p.title 225 ($y+18) 49 $navy 775 77 $true)
 $h+=(T $p.text 225 ($y+101) 42 $ink 775 69);$y+=$h+90;$i++
}
$y+=5;$boxY=$y;$boxH=762;Rect 64 $boxY 952 $boxH $white
$yy=$boxY+42;$yy+=(T '活动信息' 105 $yy 47 $navy 870 73 $true);$yy+=26
$yy+=(T ($d.date+[Environment]::NewLine+$d.time) 105 $yy 42 $ink 866 68);$yy+=27
$yy+=(T $d.location 105 $yy 43 $ink 866 69 $true)
$yy+=(T $d.address 105 ($yy+7) 38 $ink 866 61);$yy+=8
$yy+=(T $d.venue_note 105 ($yy+6) 36 $muted 866 58);$yy+=36
$yy+=(T $d.audience 105 $yy 40 $ink 866 65)
$y=$boxY+$boxH+84
$y+=(T ("带着问题来，"+[Environment]::NewLine+"带着更清楚的方向回去。") 80 $y 48 $teal 920 77 $true);$y+=85
$r.Add((Save $y '01_活动介绍.png'))
Canvas 2
Brand;Line 80 191 1000 191 $pale
$y=257;Label '02  /  拟定分享方向' $y;$y+=82
$y+=(T ("把职业选择，"+[Environment]::NewLine+"放进真实行业里。") 80 $y 76 $navy 920 106 $true);$y+=39
$y+=(T ("六个行业方向，围绕面试、路径与变化交流。"+[Environment]::NewLine+"以下为拟定分享内容。") 80 $y 42 $ink 920 69);$y+=72;$i=1
foreach($s in $d.sectors){
 $sh=MeasureContent $s.scope 39 868 60
 $rh1=MeasureContent $s.interview 40 738 62;$rh2=MeasureContent $s.path 40 738 62;$rh3=MeasureContent $s.topic 40 738 62
 $cardH=154+$sh+$rh1+$rh2+$rh3+83;Rect 64 $y 952 $cardH $white
 [void](T ('0'+$i) 105 ($y+35) 51 $rust 110 74 $false 'Georgia')
 [void](T $s.name 235 ($y+31) 56 $navy 720 81 $true)
 [void](T $s.scope 105 ($y+117) 39 $muted 868 60)
 $yy=$y+139+$sh;Line 105 $yy 975 $yy $pale 1;$yy+=25
 foreach($row in @(@('面试',$s.interview),@('路径',$s.path),@('话题',$s.topic))){
  [void](T $row[0] 105 ($yy+7) 31 $rust 90 53 $true)
  $rh=(T $row[1] 229 $yy 40 $ink 738 62);$yy+=$rh+15
 }
 $y+=$cardH+28;$i++
}
$y+=32;Rect 64 $y 952 334 $navy
[void](T '国央企就业方向也在筹备中' 105 ($y+42) 47 $white 868 73 $true)
[void](T ("具体嘉宾、分享主题与交流形式，"+[Environment]::NewLine+"将随筹备进展陆续公布。") 105 ($y+148) 41 '#D7E3E5' 868 68)
$y+=386;$y+=(T $d.event_line 80 $y 34 $muted 920 56);$y+=52;$r.Add((Save $y '02_行业分享.png'))
Canvas 3
Rect 0 0 1080 700 $navy;Brand '#F5F1E9';Line 80 191 1000 191 '#38506E'
[void](T '03  /  相聚与交流' 80 254 30 '#D9A68D' 920 48 $true)
[void](T ("把问题带来，"+[Environment]::NewLine+"与校友当面聊聊。") 80 345 75 $white 920 108 $true)
[void](T $d.event_line 80 601 34 '#D7E3E5' 920 55)
$y=791;Label '活动安排（拟）' $y;$y+=94
foreach($s in $d.schedule){
 [void](T $s.time 80 ($y+4) 35 $rust 262 56 $true);Dot 332 ($y+19) 14 $rust
 $h1=(T $s.title 386 $y 49 $navy 614 77 $true)
 $h2=(T $s.text 386 ($y+$h1+9) 40 $ink 614 65)
 $rh=[Math]::Max(178,$h1+$h2+48);Line 339 ($y+44) 339 ($y+$rh-17) '#D8C7B7';$y+=$rh
}
$y+=36;$y+=(T '你可以带着这些问题来' 80 $y 51 $navy 920 82 $true);$y+=31
foreach($q in $d.questions){Dot 82 ($y+19) 11 $rust;$y+=(T $q 127 $y 43 $ink 873 72);$y+=12}
$y+=64;Line 80 $y 1000 $y $pale;$y+=53
$y+=(T '报名与咨询' 80 $y 58 $navy 920 87 $true);$y+=24
$y+=(T '拟报名费 9.9元 / 人' 80 $y 48 $rust 920 76 $true)
$y+=(T $d.capacity 80 ($y+9) 42 $ink 920 69);$y+=48
$boxH=554;Rect 64 $y 952 $boxH $navy
[void](T '活动联系人' 105 ($y+44) 34 '#D0DEE2' 868 53)
[void](T $d.contact.name 105 ($y+124) 69 $white 868 101 $true)
[void](T $d.contact.phone 105 ($y+245) 66 $white 868 97 $true 'Georgia')
[void](T '电话 / 微信同号' 105 ($y+352) 38 '#D0DEE2' 868 61)
[void](T '请联系了解报名、支付及入场安排。' 105 ($y+450) 37 '#D0DEE2' 868 60)
$y+=$boxH+67
$y+=(T ("日期、地点已更新。时段、费用、嘉宾及具体安排，"+[Environment]::NewLine+"以最终活动通知为准。") 80 $y 36 $muted 920 60);$y+=80
$y+=(T ("从一段校友情谊，"+[Environment]::NewLine+"走向下一段职业旅程。") 80 $y 49 $teal 920 79 $true);$y+=82
$r.Add((Save $y '03_流程报名.png'))
$script:audit|ConvertTo-Json -Depth 4|Set-Content -LiteralPath (Join-Path $PSScriptRoot 'layout_audit.json') -Encoding UTF8
foreach($font in $script:fonts.Values){$font.Dispose()}
$r|ConvertTo-Json
