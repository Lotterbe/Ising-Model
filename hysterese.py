import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.animation as animation
from matplotlib.widgets import Slider
from Metropolis import Metropolis, Observables



def hysterese_measuring(external_field_list, beta=0.49):
    # 0 ist schon 'drin'
    # [0.25 ... 1, ... 0.25, 0, -0.25, ... -1, ... -0.25, 0.25, ... 1]
    magneti = []
    magneti_err = []
    metro = Metropolis(*(256, 256), beta=beta, flip=False)
    metro.itersteps = 2200 * metro.total_number_of_points
    metro.first_skip = 200 * metro.total_number_of_points
    metro.skip = 100 * metro.total_number_of_points
    metro.reset()
    configs = metro.start_simulation()
    observables = Observables(configs, beta=beta)
    observables.nabs_magnetisation()
    magneti_err.append(observables.jackknife(observables.nabs_m_per_config, 10))
    magneti.append(observables.nabs_m_average)
    #metro.itersteps = 1020 * metro.total_number_of_points
    #metro.first_skip = 20 * metro.total_number_of_points
    #metro.skip = 10 * metro.total_number_of_points
    for b_field in external_field_list:
        print(magneti)
        metro.reset()
        metro.b_ext = b_field
        configsneu = metro.start_simulation()
        observables.all_configs = configsneu
        magneti_err.append(observables.jackknife(observables.nabs_m_per_config, 10))
        # b_ext wird fuer magnetisation nicht benoetigt
        #observables.b_ext() = b_field
        observables.nabs_magnetisation()
        magneti.append(observables.nabs_m_average)
    return magneti, magneti_err


b_fields = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1, 0.11, 0.12,
            0.13, 0.14, 0.15, 0.14, 0.13, 0.12, 0.11, 0.10, 0.09, 0.08, 0.07, 0.06, 0.05, 0.04,
            0.03, 0.02, 0.01, 0, -0.01, -0.02, -0.03, -0.04, -0.05, -0.06, -0.07,
            -0.08, -0.09, -0.1, -0.11, -0.12, -0.13, -0.14, -0.15,  -0.14, -0.13,
            -0.12, -0.11, -0.10, -0.09, -0.08, -0.07, -0.06, -0.05, -0.04, -0.03,
            -0.02, -0.01,0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09,
            0.1, 0.11, 0.12, 0.13, 0.14, 0.15]
            #0.16, 0.17, 0.18, 0.19, 0.2, 0.19, 0.18, 0.17, 0.16,
            #0.15,
            #-0.16, -0.17,
            #-0.18, -0.19, -0.2, -0.19, -0.18, -0.17, -0.16, -0.15,
            #ä, 0.16, 0.17, 0.18, 0.19, 0.2
magneti_vals, magneti_err = hysterese_measuring(b_fields)
print(magneti_vals)
#werte aus der letzten hysterese
#[0.8971023559570312, 0.9008499145507812, 0.9068191528320313, 0.9094329833984375, 0.9121749877929688, 0.9152801513671875, 0.9181655883789063, 0.92039794921875, 0.9223312377929688, 0.9234466552734375, 0.9276473999023438, 0.9283401489257812, 0.9304168701171875, 0.9325439453125, 0.933148193359375, 0.9351364135742187, 0.9335189819335937, 0.9317977905273438, 0.9310470581054687, 0.928314208984375, 0.927032470703125, 0.9248870849609375, 0.9229385375976562, 0.9201507568359375, 0.9174057006835937, 0.916278076171875, 0.9128402709960938, 0.9082656860351562, 0.905029296875, 0.9004776000976562, 0.8964508056640625, 0.8905487060546875, 0.880438232421875, 0.5385879516601563, -0.8015274047851563, -0.9154510498046875, -0.9184188842773438, -0.9207611083984375, -0.9224273681640625, -0.924359130859375, -0.926373291015625, -0.9281875610351562, -0.93013916015625, -0.9312225341796875, -0.932403564453125, -0.934967041015625, -0.9342330932617188, -0.9318817138671875, -0.9301345825195313, -0.9278610229492188, -0.9264846801757812, -0.9249588012695312, -0.9225845336914062, -0.920074462890625, -0.9178390502929688, -0.9155426025390625, -0.911810302734375, -0.90841064453125, -0.9046340942382812, -0.9017913818359375, -0.8979049682617187, -0.8902740478515625, -0.8741226196289062, -0.6992218017578125, 0.6101470947265625, 0.9152618408203125, 0.9171249389648437, 0.9204254150390625, 0.9225296020507813, 0.9237762451171875, 0.9270477294921875, 0.928912353515625, 0.9306808471679687, 0.9312484741210938, 0.93338623046875, 0.9351638793945313]
x_vals = [0, *b_fields]
print(np.array(magneti_err)/np.array(magneti_vals)*100)
plt.plot(x_vals, magneti_vals, marker='+')
plt.show()
