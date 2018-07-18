#!/usr/bin/env python
# -*- coding utf-8 -*-

from __future__ import print_function


"""Python port of http://gnuplot.info/scripts/99bottles.gp

The implementation could be simpler using only Python variables but it shows
that functions and variables can flow from Python to Gnuplot and vice-versa

"""
if __name__ == '__main__':

    import argparse
    import newplot

    parser = argparse.ArgumentParser(description='Python port of 99bottles.gp :'
                                     ' http://gnuplot.info/scripts/99bottles.gp')
    parser.add_argument('max_bottles', type=int, default=99,
                        help='Maximum number of bottles')
    args = parser.parse_args()
    if args.max_bottles > 99 or args.max_bottles <= 0:
        raise ValueError("This is the 99 bottles song, so 'max_bottles' must be"
                         " in [1:99]")
    
    with newplot.Gnuplot() as gp:
        # Define a maximum number of bottles in case we do not want the whole
        # song.
        gp.max = args.max_bottles
        # Initialize the plot only once (bottles is undefined on first entry).
        # Open the "dumb" terminal to generate ascii art
        # Define the plot layout such that there are 99 character slots for
        # bottles, leaving room for a margin and a shelf-divider at each end.
        fig = gp.Figure(title='99 bottles song', term='dumb',
                        options=('size 104, 6',))
        fig.set('xtics', None)
        fig.set('ytics', None)
        fig.set('key', None)
        fig.set('border', '1 front')
        fig.set('lmargin', 1)
        fig.set('rmargin', 1)
        fig.set('xrange', '[0:100]')
        fig.set('yrange', '[-1:1]')
        # Create and initialize the bottles counter
        gp.bottles = gp.max
        # String valued function to create the "bottle(s)" string
        # To decide wether we should a plural 's' a dirty substring trick
        # is used, but we could always use a ternary operator instead
        # Note that there is no name conflict with the bottles variable.
        gp._bottles = gp.function(['b'], '"bottle" . "s"[0:(b != 1)]')
        # Function which returns the number b or the string "no more" iff b=0.
        # The case of the first letter can be switched by the parameter c.
        # Please note that this function can be string or number valued.
        gp.number = gp.function(['b', 'c'],
                                '(b > 0) ? sprintf("%d",b) : '\
                                           '"nN"[c+1:c+1] . "o more"')
        while gp.bottles >= 0:
            # We use a ternary operator to decide what to do next ;-)
            gp.action = \
                '(bottles != 0) ? "Take one down and pass it around":'\
                                  '"Go to the store and buy some more"'
            # Write the new verse into a label
            # On the sceond line the modulo trick is used to wrap around the
            # number of bottles
            gp.Label1 = 'sprintf("%s %s of beer on the wall, %s %s of ' \
                             'beer.\\n", number(bottles,1), _bottles(bottles),' \
                             ' number(bottles,0), _bottles(bottles))'
            gp.Label2 = 'action . ", " . sprintf("%s %s of beer on the ' \
                            'wall.", number((bottles + max) % (max + 1), 0), '\
                            '_bottles(bottles-1))'

            # Use the verse as a label for the x-axis
            fig.set('xlabel', 'Label1.Label2', 'offset 0,-1')

            # We will use the sampling grid to control how many bottles are
            # drawn. But the set of samples always includes the two end points,
            # which we don't want.  So we over-write the endpoints with shelf
            # dividers.
            fig.set('label', '1', '"|" at 0,1 front')
            fig.set('label', '2', '"|" at 100,1 front')
            
            # Draw the shelf
            # In the "dumb" terminal, linetype 6 is an ampersand 
            fig.set('samples', 'bottles+2')
            fig.plot('1', _with='impulses linetype 6')
            print(fig.submit())
            gp.bottles = gp.bottles - 1
