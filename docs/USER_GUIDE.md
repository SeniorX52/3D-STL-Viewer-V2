# 3D Insole Adapter - User Guide

**Author:** Mostafa Abdelaziz

## Welcome!

The **3D Insole Adapter** is a desktop application designed for orthotic professionals to create custom-fitted insoles. This guide will walk you through every feature of the application in simple, easy-to-understand terms.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Understanding the Interface](#understanding-the-interface)
3. [Loading Your Files](#loading-your-files)
4. [Placing Reference Points](#placing-reference-points)
5. [Scaling the Insole](#scaling-the-insole)
6. [Mirroring for Left/Right Foot](#mirroring-for-leftright-foot)
7. [Adding Text Labels](#adding-text-labels)
8. [Exporting Your Insole](#exporting-your-insole)
9. [Tips and Best Practices](#tips-and-best-practices)
10. [Troubleshooting](#troubleshooting)

---

## Getting Started

### System Requirements
- Windows 10 or Windows 11
- 4GB RAM minimum (8GB recommended)
- Graphics card with OpenGL support (most modern computers)
- 500MB free disk space

### Installation
1. Download `InsoleAdapter_Setup.exe` from the provided link
2. Double-click to run the installer
3. Follow the on-screen instructions
4. Launch from the Start Menu or Desktop shortcut

**No additional software is required** - everything is included in the installer.

---

## Understanding the Interface

When you open the application, you'll see two main areas:

```
┌─────────────────────────────────────────────────────────────────┐
│  File  View  Help                                               │
├──────────────────────┬──────────────────────────────────────────┤
│                      │                                          │
│   CONTROL PANEL      │           3D VIEWER                      │
│                      │                                          │
│  • File Loading      │     [Your 3D models appear here]         │
│  • Reference Points  │                                          │
│  • Scaling           │     Mouse Controls:                      │
│  • Mirror            │     • Left-click + drag = Rotate         │
│  • Position          │     • Right-click + drag = Pan           │
│  • Text Label        │     • Scroll wheel = Zoom                │
│  • Export            │                                          │
│                      │                                          │
└──────────────────────┴──────────────────────────────────────────┘
```

### Control Panel (Left Side)
All the tools you need to adapt your insole, organized in logical sections.

### 3D Viewer (Right Side)
Interactive 3D view of your foot scan and insole. You can rotate, pan, and zoom to see your work from any angle.

---

## Loading Your Files

### Step 1: Load the Foot Scan

1. In the **"File Loading"** section, click **"Load Foot"**
2. Navigate to your foot scan STL file
3. Select the file and click **"Open"**
4. The foot will appear in the 3D viewer (skin-colored by default)

### Step 2: Load the Insole Template

1. Click **"Load Insole"**
2. Navigate to your insole template STL file
3. Select the file and click **"Open"**
4. The insole will appear overlaid on the foot (blue by default)

**Tip:** The insole may not be perfectly positioned at first - that's normal! You'll align it in the next steps.

---

## Placing Reference Points

Reference points help the software understand the size and shape of the foot.

### The Three Reference Points:

1. **Heel** - The back center of the heel
2. **1st Metatarsal** - The ball of the foot under the big toe
3. **5th Metatarsal** - The ball of the foot under the little toe

### How to Place Points:

1. Click **"Start Picking Points"** (button turns green)
2. The foot becomes slightly transparent to help you see better
3. **Click on the heel** - a red sphere appears marking the point
4. **Click on the 1st metatarsal** - another marker appears
5. **Click on the 5th metatarsal** - the final marker appears
6. The status shows "Points: 3/3" when complete

### What Happens Next:
- The software calculates **foot length** (heel to toe)
- The software calculates **foot width** (across the metatarsals)
- These measurements are displayed in the interface

**Made a mistake?** Click **"Clear Points"** to start over.

---

## Scaling the Insole

Once you have your reference points, you can scale the insole to fit the foot.

### Automatic Scaling (Recommended)

1. Click **"Align Insole to Foot"** to position the insole correctly
2. Click **"Auto Scale to Foot"** to match the insole size to your foot measurements
3. The insole will resize to match the foot dimensions

### Manual Fine-Tuning

If you need precise control:

| Control | What It Does |
|---------|--------------|
| **Insole Scale X** | Makes insole wider or narrower |
| **Insole Scale Y** | Makes insole longer or shorter |
| **Insole Scale Z** | Makes insole thicker or thinner |

Use the spinboxes to set exact values, then click **"Apply Insole Scale"**.

### Foot Scale (Combined Scaling)

The **"Foot Scale"** slider scales both the foot AND the insole together. This is useful if you need to adjust the overall size while keeping proportions correct.

**Reset:** Click **"Reset Insole"** to restore the original insole size.

---

## Mirroring for Left/Right Foot

Insoles are often designed for one foot and need to be flipped for the other.

### How to Mirror:

| Button | What It Does |
|--------|--------------|
| **Mirror X** | Flips the insole left-to-right |
| **Mirror Y (L↔R)** | Flips the insole front-to-back (most common for foot swapping) |

Click the appropriate button to flip your insole for the opposite foot.

---

## Adding Text Labels

You can add patient information directly onto the insole surface. The text can be **embossed** (raised) or **engraved** (cut into) the surface.

### Label Information:

| Field | Description |
|-------|-------------|
| **Name** | Patient or client name |
| **Side** | L (Left) or R (Right) |
| **Date** | Automatically filled with today's date |

### Placing the Label:

1. **Enter the patient name** in the "Name" field
2. **Select the side** (L or R)
3. **Click "Pick Label Position"** - the cursor changes to a crosshair
4. **Click on the insole surface** where you want the label
   - A green marker shows where the label will be placed
   - You can click on the **side** of the insole for curved labels!
5. **Adjust settings** if needed:
   - **Font Size** - How big the text is (in mm)
   - **Depth** - How deep the engraving/embossing is
   - **Offset X/Y** - Move the label left/right or up/down
   - **Rotation** - Angle the text
   - **Mirror Horizontal** - Flip text left-right if it appears backwards
   - **Mirror Vertical** - Flip text up-down if it appears upside down
6. **Click "Apply Label to Insole"**

### Emboss vs Engrave:

| Option | Result |
|--------|--------|
| **Emboss** (default) | Text sticks OUT from the surface |
| **Engrave** (checked) | Text is CUT INTO the surface |

### Mirror Options:

If your label appears backwards or upside down on a curved surface:

| Option | When to Use |
|--------|-------------|
| **Mirror Horizontal** | Text appears backwards (like in a mirror) |
| **Mirror Vertical** | Text appears upside down |

**Tip:** The label automatically wraps around curved surfaces like the side of the insole!

---

## Exporting Your Insole

When you're happy with your adapted insole:

1. Click **"Export Adapted Insole as STL"**
2. Choose where to save the file
3. The filename is auto-generated: `Name_L_2026-01-11_insole.stl`
4. Click **"Save"**

**Uncheck "Auto-generate filename"** if you want to name the file yourself.

---

## Tips and Best Practices

### For Best Results:

1. **Quality Scans** - Use high-quality foot scans for accurate fitting
2. **Proper Orientation** - Ensure the foot scan is oriented correctly (toes forward)
3. **Reference Points** - Place points carefully for accurate measurements
4. **Check All Angles** - Rotate the 3D view to verify the fit from all sides
5. **Test Exports** - Open exported files in another 3D viewer to verify

### Keyboard Shortcuts:

| Key | Action |
|-----|--------|
| **R** | Reset view |
| **T** | Top view |
| **F** | Front view |
| **I** | Isometric view |
| **P** | Toggle settings panel |
| **1** | Wireframe mode |
| **2** | Solid mode |
| **3** | Points mode |
| **Ctrl+O** | Open foot STL |
| **Ctrl+I** | Open insole STL |
| **Ctrl+E** | Export insole |

---

## Troubleshooting

### "The insole appears in the wrong position"
- Click **"Align Insole to Foot"** to reposition
- Use the Position/Rotation sliders to adjust manually

### "The label doesn't appear"
- Make sure you've entered a name
- Click "Pick Label Position" first, then click on the insole
- Try clicking on a different area of the insole

### "The export file is empty or corrupted"
- Make sure an insole is loaded
- Try exporting to a different location
- Check that you have write permissions to the folder

### "The 3D view is slow"
- Reduce the "Foot Opacity" slider
- Use "Solid" render mode instead of "Solid + Edges"
- Close other applications to free up memory

### "Colors look wrong"
- Click the color buttons in "View Settings" to customize
- Try changing the render mode

---

## Getting Help

If you encounter issues not covered in this guide:

1. Check the **Help → Instructions** menu in the application
2. Contact technical support with:
   - Description of the problem
   - Screenshots if possible
   - The STL files you're working with

---

*Thank you for using 3D Insole Adapter!*
