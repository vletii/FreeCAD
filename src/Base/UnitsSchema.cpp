/***************************************************************************
 *   Copyright (c) 2009 Jürgen Riegel <FreeCAD@juergen-riegel.net>         *
 *                                                                         *
 *   This file is part of the FreeCAD CAx development system.              *
 *                                                                         *
 *   This library is free software; you can redistribute it and/or         *
 *   modify it under the terms of the GNU Library General Public           *
 *   License as published by the Free Software Foundation; either          *
 *   version 2 of the License, or (at your option) any later version.      *
 *                                                                         *
 *   This library  is distributed in the hope that it will be useful,      *
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
 *   GNU Library General Public License for more details.                  *
 *                                                                         *
 *   You should have received a copy of the GNU Library General Public     *
 *   License along with this library; see the file COPYING.LIB. If not,    *
 *   write to the Free Software Foundation, Inc., 59 Temple Place,         *
 *   Suite 330, Boston, MA  02111-1307, USA                                *
 *                                                                         *
 ***************************************************************************/

#include "PreCompiled.h"
#ifdef __GNUC__
#include <unistd.h>
#endif

#include <QLocale>
#include <QString>

#include "Quantity.h"
#include "UnitsSchema.h"

using namespace Base;

std::string UnitsSchema::toLocale(const Base::Quantity& quant,
                                  double factor,
                                  const std::string& unitString) const
{
    QLocale Lc;
    const QuantityFormat& format = quant.getFormat();
    if (format.option != QuantityFormat::None) {
        int opt = format.option;
        Lc.setNumberOptions(static_cast<QLocale::NumberOptions>(opt));
    }

    QString Ln = Lc.toString((quant.getValue() / factor), format.toFormat(), format.precision);
    return QStringLiteral("%1 %2").arg(Ln, QString::fromStdString(unitString)).toStdString();
}
