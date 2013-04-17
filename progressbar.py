import sys
from doxysettings import DocSettings

progressbar_counter = 0

def progressbar(done, total):
    if DocSettings.args.quiet:
        return

    global progressbar_counter
    progressbar_counter += 1

    sys.stdout.write("\r")

    width = 80

    tail = " [" + str(done) + "/" + str(total) + "]"

    consoleMargin = 20
    maxDot = width - len(tail) - consoleMargin
    for x in range(0, done * maxDot / total):
        sys.stdout.write('*')

    sys.stdout.write(tail)

    if(progressbar_counter > 0):
        progressbar_counter = 0
        sys.stdout.flush()

    # Newline at last item
    if done == total:
        print("")
