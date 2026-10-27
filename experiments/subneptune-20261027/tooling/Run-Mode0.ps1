param(
 [string]$Table="$PSScriptRoot\demo_cases.csv",
 [string]$Output,
 [string]$Repo='D:\GPT\projects\Sub-Neptune\work\magrathea-mode0-clean-20261025-a17b',
 [switch]$Resume,
 [int]$Limit=0,
 [ValidateRange(1,3600)][int]$TimeoutSeconds=45
)
$ErrorActionPreference='Stop'
function LinuxPath([string]$Value){
 $absolute=[IO.Path]::GetFullPath($Value)
 if($absolute -notmatch '^([A-Za-z]):\\'){throw 'A local drive path is required'}
 return '/mnt/'+$Matches[1].ToLower()+'/'+$absolute.Substring(3).Replace('\','/')
}
if(-not $Output){$Output='D:\GPT\projects\Sub-Neptune\outputs\mode0-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+[Guid]::NewGuid().ToString('N').Substring(0,6)}
if([IO.Path]::GetFullPath($Output) -notmatch '^D:\\'){throw 'New output must be on D:'}
$template='D:\GPT\projects\Sub-Neptune\Magrathea\experiments\archive\20261018\literature-cases\configs\gasdwarf_1pct_ideal_gas.cfg'
$arguments=@('-d','Ubuntu','--exec','python3','-B',(LinuxPath "$PSScriptRoot\mode0_batch.py"),'--repo',(LinuxPath $Repo),'--table',(LinuxPath $Table),'--template',(LinuxPath $template),'--output',(LinuxPath $Output),'--timeout',"$TimeoutSeconds")
if($Resume){$arguments+='--resume'}
if($Limit -gt 0){$arguments+=@('--limit',"$Limit")}
& wsl.exe @arguments
if($LASTEXITCODE -ne 0){throw "Batch stopped (exit $LASTEXITCODE). Existing attempts were preserved."}
Write-Output "Results: $Output"
