# Only list files Git considers part of the project
$files = git ls-files --others --cached --exclude-standard

# Print as a basic tree structure
function Show-Tree {
    param ([string[]]$Files)

    $grouped = $Files | Group-Object { Split-Path $_ }
    foreach ($group in $grouped) {
        if ($group.Name) {
            Write-Output "$($group.Name)\"
        } else {
            Write-Output ".\"
        }
        foreach ($file in $group.Group) {
            Write-Output "  -- $(Split-Path $file -Leaf)"
        }
    }
}

# Generate and save the tree
$tree = Show-Tree -Files $files
$tree | Out-File -FilePath "project_structure.txt" -Encoding UTF8
