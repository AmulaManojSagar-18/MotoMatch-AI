# Script to download bike images from official sources
# Run from frontend/ directory: .\scripts\download-bike-images.ps1

$ErrorActionPreference = "Continue"

# Output directory
$outputDir = "$PSScriptRoot\..\public\bikes"
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}

# Bike image mappings (filename and direct image URLs)
$bikes = @(
    @{
        filename = "hero-splendor-plus.png"
        url = "https://www.heromotocorp.com/content/dam/hero-aem-website/in/en-in/bikes/splendor-plus/hero-splendor-plus.jpg"
    },
    @{
        filename = "hero-xpulse-200-4v.png"
        url = "https://www.bikewale.com/hero-bikes/xpulse-200-4v/images/hero-xpulse-200-4v-right-side-view-501043/"
    },
    @{
        filename = "tvs-ronin-225.png"
        url = "https://www.tvsmotor.com/content/dam/tvs-motor/tvs-ronin-225-td.jpg"
    },
    @{
        filename = "yamaha-r15-v4.png"
        url = "https://www.yamaha-motor-india.com/content/dam/yamaha-motor-india/product/yzf-r15-v4/2026/01/1/0/147/YZF-R15-V4-01.jpg"
    },
    @{
        filename = "royal-enfield-hunter-350.png"
        url = "https://www.royalenfield.com/content/dam/royal-enfield/hunter-350/hunter-350-right-side-view.jpg"
    },
    @{
        filename = "honda-cb350.png"
        url = "https://www.honda.co.in/content/dam/honda/Motorcycles/CB350/CB350-Side-View.png"
    },
    @{
        filename = "triumph-speed-400.png"
        url = "https://www.triumphmotorcycles.in/content/dam/triumph-motorcycles/models/speed-400/speed-400-right-side-view.jpg"
    },
    @{
        filename = "bajaj-pulsar-ns400z.png"
        url = "https://www.bajajauto.com/content/dam/bajaj/auto/bikes/pulsar-ns400z/pulsar-ns400z-right-side-view.png"
    },
    @{
        filename = "royal-enfield-guerrilla-450.png"
        url = "https://www.royalenfield.com/content/dam/royal-enfield/guerrilla-450/guerrilla-450-right-side-view.jpg"
    },
    @{
        filename = "royal-enfield-continental-gt-650.png"
        url = "https://www.royalenfield.com/content/dam/royal-enfield/continental-gt-650/continental-gt-650-right-side-view.jpg"
    }
)

Write-Host "Downloading bike images to: $outputDir"
Write-Host "========================================`n"

$downloaded = 0
$failed = 0

foreach ($bike in $bikes) {
    $filePath = Join-Path $outputDir $bike.filename
    
    if (Test-Path $filePath) {
        Write-Host "[SKIPPED] $($bike.filename) - Already exists"
        continue
    }
    
    Write-Host "[DOWNLOADING] $($bike.filename)..."
    
    try {
        $webClient = New-Object System.Net.WebClient
        $webClient.Headers.Add("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        # Try direct download first
        $webClient.DownloadFile($bike.url, $filePath)
        
        if (Test-Path $filePath) {
            $size = (Get-Item $filePath).Length
            Write-Host "[SUCCESS] $($bike.filename) - ${size} bytes`n"
            $downloaded++
        } else {
            Write-Host "[FAILED] $($bike.filename) - Download returned empty file`n"
            $failed++
        }
    }
    catch {
        Write-Host "[FAILED] $($bike.filename) - $($_.Exception.Message)`n"
        $failed++
    }
}

Write-Host "========================================"
Write-Host "Summary: $downloaded downloaded, $failed failed"
Write-Host "Note: If some downloads failed, you can manually download from:"
Write-Host "  - Hero: https://www.heromotocorp.com"
Write-Host "  - TVS: https://www.tvsmotor.com"
Write-Host "  - Yamaha: https://www.yamaha-motor-india.com"
Write-Host "  - Royal Enfield: https://www.royalenfield.com"
Write-Host "  - Honda: https://www.honda.co.in"
Write-Host "  - Triumph: https://www.triumphmotorcycles.in"
Write-Host "  - Bajaj: https://www.bajajauto.com"
